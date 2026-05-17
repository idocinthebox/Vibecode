import * as vscode from 'vscode';

export class AgentDetectionService implements vscode.Disposable {
  private readonly emitter = new vscode.EventEmitter<string>();
  private timer: NodeJS.Timeout | undefined;
  private lastAgent: string | undefined;

  readonly onAgentSessionStarted: vscode.Event<string> = this.emitter.event;

  register(): vscode.Disposable[] {
    const disposables: vscode.Disposable[] = [];

    disposables.push(
      vscode.window.onDidChangeActiveTextEditor(() => {
        this.checkActiveAgent();
      })
    );

    disposables.push(
      vscode.workspace.onDidChangeConfiguration((e) => {
        if (e.affectsConfiguration('vibeCode.attribution.agentExtensionIds')) {
          this.checkActiveAgent();
        }
      })
    );

    this.timer = setInterval(() => this.checkActiveAgent(), 5000);
    this.checkActiveAgent();

    return disposables;
  }

  private checkActiveAgent(): void {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      return;
    }

    const cfg = vscode.workspace.getConfiguration('vibeCode');
    const extensionIds = cfg.get<string[]>('attribution.agentExtensionIds', [
      'GitHub.copilot',
      'GitHub.copilot-chat',
      'openai.openai-codex',
      'openai.chatgpt',
      'anysphere.cursorpyright',
      'Cursor.cursor',
      'google.antigravity',
      'anthropic.claude-code',
    ]);

    for (const id of extensionIds) {
      const ext = vscode.extensions.getExtension(id);
      if (ext?.isActive) {
        if (this.lastAgent !== id) {
          this.lastAgent = id;
          this.emitter.fire(id);
        }
        return;
      }
    }

    this.lastAgent = undefined;
  }

  dispose(): void {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = undefined;
    }
    this.emitter.dispose();
  }
}
