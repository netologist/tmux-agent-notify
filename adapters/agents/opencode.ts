import { spawn } from "node:child_process";
import { join } from "node:path";
import type { Plugin } from "@opencode-ai/plugin";

export const TmuxAgentNotify: Plugin = async ({ client }) => {
  const sessions = new Map<string, { active: boolean; generation: number }>();

  return {
    event: async ({ event }) => {
      if (event.type === "session.deleted") {
        sessions.delete(event.properties.info.id);
        return;
      }
      if (event.type !== "session.status") return;

      const { sessionID, status } = event.properties;
      let state = sessions.get(sessionID);
      if (status.type === "busy" || status.type === "retry") {
        if (!state) {
          state = { active: true, generation: 1 };
          sessions.set(sessionID, state);
        } else if (!state.active) {
          state.active = true;
          state.generation++;
        }
        return;
      }
      // Ignore idle at startup and duplicate idle events.
      if (!state?.active || !process.env.HOME) return;
      state.active = false;
      const generation = state.generation;

      try {
        const { data } = await client.session.get({ path: { id: sessionID } });
        // Skip subagents and stale lookups after a new run or session deletion.
        if (!data || data.parentID || sessions.get(sessionID) !== state || state.active || state.generation !== generation) return;
        const child = spawn(join(process.env.HOME, ".config/tmux/agent-notify/notify.sh"), ["opencode"], {
          detached: true,
          stdio: "ignore",
        });
        child.on("error", () => {});
        child.unref();
      } catch {
        // A missing session or notifier must never interrupt the agent.
      }
    },
  };
};
