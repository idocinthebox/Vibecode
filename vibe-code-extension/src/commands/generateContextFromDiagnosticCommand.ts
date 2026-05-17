import * as vscode from 'vscode';
import { VibeCodeApiClient } from '../services/apiClient';
import { ConfigService } from '../services/configService';
import { WorkspaceService } from '../services/workspaceService';
import { TokenStatusService } from '../services/tokenStatusService';
import { VibeCodeDiagnosticData } from '../types/diagnostics';
import { getLogger } from '../ui/outputChannel';
import { showError, showInfo } from '../ui/notifications';

export function registerGenerateContextFromDiagnosticCommand(
  context: vscode.ExtensionContext,
  api: VibeCodeApiClient,
  workspace: WorkspaceService,
  config: ConfigService,
  tokenStatus: TokenStatusService
): vscode.Disposable {
  return vscode.commands.registerCommand(
    'vibeCode.generateContextFromDiagnostic',
    async (data?: VibeCodeDiagnosticData) => {
      const logger = getLogger();
      logger.info('Command: generateContextFromDiagnostic');

      if (!data) {
        showError(new Error('No diagnostic data provided'));
        return;
      }

      try {
        const cfg = config.getConfig();
        const projectRoot = workspace.getProjectRoot();

        const response = await api.injectContext({
          query: data.preventionRule || data.memoryId,
          project_path: projectRoot,
          agent_profile: cfg.defaultAgentProfile,
          max_context_tokens: cfg.maxInjectedTokens,
          include_failure_warnings: cfg.includeFailureWarnings,
          include_project_rules: true,
          include_success_patterns: true,
        });

        const doc = await vscode.workspace.openTextDocument({
          language: 'markdown',
          content: response.context_markdown,
        });
        await vscode.window.showTextDocument(doc, { preview: false });

        tokenStatus.reportSavings(response.estimated_tokens_saved);
        showInfo(
          `Context generated: ~${response.estimated_context_tokens} tokens`
        );
      } catch (err) {
        logger.error(`generateContextFromDiagnostic failed: ${err}`);
        showError(err as Error);
        tokenStatus.setOffline();
      }
    }
  );
}
