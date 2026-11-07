import { spawn } from "node:child_process";
import { join } from "node:path";
import type { ExtensionAPI } from "@oh-my-pi/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.on("agent_end", (event, ctx) => {
    // Child sessions share extension factories. A nested omp also inherits OMPCODE.
    if (ctx.mode !== "tui" || ctx.agent.kind !== "main" || process.env.OMPCODE === "1" || event.willContinue) return;
    if (!process.env.HOME) return;

    try {
      const child = spawn(join(process.env.HOME, ".config/tmux/agent-notify/notify.sh"), ["omp"], {
        detached: true,
        stdio: "ignore",
      });
      child.on("error", () => {});
      child.unref();
    } catch {
      // Notifications must never interrupt the agent.
    }
  });
}
