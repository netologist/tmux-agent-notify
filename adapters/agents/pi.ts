import { spawn } from "node:child_process";
import { join } from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.on("agent_settled", (_event, ctx) => {
    // Headless child agents normally run in print/JSON mode, not the pane's TUI.
    if (ctx.mode !== "tui" || !ctx.isIdle() || !process.env.HOME) return;

    try {
      const child = spawn(join(process.env.HOME, ".config/tmux/agent-notify/notify.sh"), ["pi"], {
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
