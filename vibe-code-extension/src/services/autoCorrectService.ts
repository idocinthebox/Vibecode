import * as fs from 'fs';
import * as path from 'path';
import * as vscode from 'vscode';
import { VibeCodeApiClient } from './apiClient';
import { AgentDetectionService } from './agentDetectionService';
import { ConfigService } from './configService';
import { DocumentContextService } from './documentContextService';
import { WorkspaceService } from './workspaceService';

export class AutoCorrectService implements vscode.Disposable {
  private readonly lastWriteByFile = new Map<string, number>();

  constructor(
    private readonly api: VibeCodeApiClient,
    private readonly config: ConfigService,
    private readonly workspace: WorkspaceService,
    private readonly contextService: DocumentContextService,
    private readonly detection: AgentDetectionService
  ) {}

  register(): vscode.Disposable[] {
    const disposables: vscode.Disposable[] = [];

    disposables.push(
      this.detection.onAgentSessionStarted(async () => {
        await this.generateContextForActiveFile();
      })
    );

    return disposables;
  }

  private async generateContextForActiveFile(): Promise<void> {
    const enabled = vscode.workspace
      .getConfiguration('vibeCode.autoCorrect')
      .get<boolean>('enabled', true);
    if (!enabled) {
      return;
    }

    const editor = vscode.window.activeTextEditor;
    if (!editor || editor.document.uri.scheme !== 'file') {
      return;
    }

    const filePath = editor.document.uri.fsPath;
    const now = Date.now();
    const prev = this.lastWriteByFile.get(filePath) || 0;
    if (now - prev < 30000) {
      return;
    }

    const cfg = this.config.getConfig();
    const query = this.contextService.buildQuery(editor.document, editor.selection);
    const injected = await this.api.injectContext({
      query,
      project_path: this.workspace.getProjectRoot(),
      agent_profile: cfg.defaultAgentProfile,
      max_context_tokens: cfg.maxInjectedTokens,
      include_failure_warnings: true,
      include_project_rules: true,
      include_success_patterns: true,
    });

    const workspaceRoot = this.workspace.getWorkspaceRoot();
    const dir = path.join(workspaceRoot, '.vibecode');
    const file = path.join(dir, 'agent-context.md');
    fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(file, injected.context_markdown, 'utf-8');

    const nowDate = new Date();
    fs.utimesSync(file, nowDate, nowDate);
    this.lastWriteByFile.set(filePath, now);
  }

  dispose(): void {
    this.lastWriteByFile.clear();
  }
}
