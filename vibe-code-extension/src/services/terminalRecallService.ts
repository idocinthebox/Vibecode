import * as vscode from 'vscode';
import { VibeCodeApiClient } from './apiClient';

/**
 * Hooks into VS Code terminal execution events.
 * When a shell command exits with a non-zero code and auto-recall is enabled,
 * queries the local VibeCode service for matching failure patterns and surfaces
 * the results as an information message.
 */
export class TerminalRecallService {
  private disposable: vscode.Disposable | undefined;

  constructor(
    private readonly api: VibeCodeApiClient,
    private readonly workspaceFolders: () => readonly vscode.WorkspaceFolder[] | undefined,
    private readonly getConfig: () => vscode.WorkspaceConfiguration,
  ) {}

  register(context: vscode.ExtensionContext): void {
    // onDidEndTerminalShellExecution is available from VS Code 1.93+
    const eventApi = (vscode.window as unknown as {
      onDidEndTerminalShellExecution?: (
        handler: (e: {
          terminal: vscode.Terminal;
          exitCode: number | undefined;
          execution: { commandLine: { value: string } };
        }) => void,
      ) => vscode.Disposable;
    }).onDidEndTerminalShellExecution;

    if (!eventApi) {
      // API not available in this VS Code version — silently skip
      return;
    }

    this.disposable = eventApi(async (e) => {
      const exitCode = e.exitCode ?? 0;
      if (exitCode === 0) {
        return;
      }

      const cfg = this.getConfig();
      const enabled = cfg.get<boolean>('autoRecall.enabled', true);
      if (!enabled) {
        return;
      }

      const command = e.execution?.commandLine?.value ?? '';
      const tail = await this._captureTail(e.execution);
      const errorOutput = tail || `Command failed: ${command}`;
      const folders = this.workspaceFolders();
      const projectPath = folders?.[0]?.uri?.fsPath;

      // Fire-and-forget with error swallow — must never block or crash the extension
      this._recallForError(errorOutput, command, projectPath).catch(() => {/* silently ignore */});
    });

    context.subscriptions.push(this.disposable);
  }

  private async _captureTail(execution: any, maxBytes = 4096): Promise<string> {
    if (typeof execution?.read !== 'function') {
      return '';
    }

    let buf = '';
    try {
      for await (const chunk of execution.read()) {
        buf += typeof chunk === 'string' ? chunk : Buffer.from(chunk).toString('utf8');
        if (buf.length > maxBytes * 4) {
          buf = buf.slice(-maxBytes * 2);
        }
      }
    } catch {
      // ignore terminal stream failures
    }

    return buf.replace(/\x1B\[[0-?]*[ -/]*[@-~]/g, '').slice(-maxBytes);
  }

  private async _recallForError(errorOutput: string, command: string, projectPath: string | undefined): Promise<void> {
    try {
      const result = await this.api.autoRecallOnError({
        error_output: errorOutput,
        project_path: projectPath,
        command,
      });

      if (result.total === 0) {
        return;
      }

      const topMatch = result.results[0];
      const moreText = result.total > 1 ? ` (+${result.total - 1} more)` : '';
      const message = `VibeCode: command \`${command}\` failed — ${topMatch.title}${moreText}`;

      const action = await vscode.window.showInformationMessage(message, 'Show Patterns');
      if (action === 'Show Patterns') {
        await vscode.commands.executeCommand('vibeCode.openReviewQueue');
      }
    } catch {
      // Network failure, service not running — silently ignore
    }
  }

  dispose(): void {
    this.disposable?.dispose();
  }
}
