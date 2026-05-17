import * as vscode from 'vscode';
import { VibeCodeApiClient } from '../services/apiClient';
import { WorkspaceService } from '../services/workspaceService';
import { ConfigService } from '../services/configService';
import { TokenStatusService } from '../services/tokenStatusService';
import { getLogger } from '../ui/outputChannel';
import { showError, showInfo } from '../ui/notifications';

export function registerInjectContextCommand(
  context: vscode.ExtensionContext,
  api: VibeCodeApiClient,
  workspace: WorkspaceService,
  config: ConfigService,
  tokenStatus: TokenStatusService
): vscode.Disposable {
  return vscode.commands.registerCommand('vibeCode.injectContext', async () => {
    const logger = getLogger();
    logger.info('Command: injectContext');

    if (!config.isEnabled()) {
      showInfo('VibeCode is disabled. Enable it in settings.');
      return;
    }

    const query = await vscode.window.showInputBox({
      prompt: 'Describe the task for agent context',
      placeHolder: 'e.g. "fix restore page mpv preview"',
    });

    if (!query) {
      return;
    }

    try {
      const cfg = config.getConfig();
      const projectRoot = workspace.getProjectRoot();

      logger.info(`Injecting context for: "${query}"`);
      const response = await api.injectContext({
        query,
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
      logger.info(
        `Context injected: ${response.estimated_context_tokens} tokens, ${response.estimated_tokens_saved} saved`
      );
      showInfo(
        `Context generated: ~${response.estimated_context_tokens} tokens, ${response.estimated_tokens_saved} saved`
      );
    } catch (err) {
      logger.error(`injectContext failed: ${err}`);
      showError(err as Error);
      tokenStatus.setOffline();
    }
  });
}
