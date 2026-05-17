import * as vscode from 'vscode';
import { VibeCodeApiClient } from '../services/apiClient';
import { WorkspaceService } from '../services/workspaceService';
import { ConfigService } from '../services/configService';
import { getLogger } from '../ui/outputChannel';
import { showSearchResultsQuickPick } from '../ui/quickPickViews';
import { showError, showInfo } from '../ui/notifications';
import { SearchMemoryResult } from '../types/api';

export function registerSearchMemoryCommand(
  context: vscode.ExtensionContext,
  api: VibeCodeApiClient,
  workspace: WorkspaceService,
  config: ConfigService
): vscode.Disposable {
  return vscode.commands.registerCommand('vibeCode.searchMemory', async () => {
    const logger = getLogger();
    logger.info('Command: searchMemory');

    if (!config.isEnabled()) {
      showInfo('VibeCode is disabled. Enable it in settings.');
      return;
    }

    const query = await vscode.window.showInputBox({
      prompt: 'Search VibeCode memory',
      placeHolder: 'e.g. "restore page audio preview"',
    });

    if (!query) {
      return;
    }

    try {
      const projectRoot = workspace.getProjectRoot();
      const language = workspace.getActiveLanguageId();

      logger.info(`Searching: "${query}" in ${projectRoot}`);
      const response = await api.searchMemory({
        query,
        project_path: projectRoot,
        language: language || undefined,
        max_results: 10,
      });

      if (response.results.length === 0) {
        showInfo('No memory results found.');
        return;
      }

      const selected = await showSearchResultsQuickPick(response.results);
      if (selected) {
        await showResultDetail(selected);
      }
    } catch (err) {
      logger.error(`searchMemory failed: ${err}`);
      showError(err as Error);
    }
  });
}

async function showResultDetail(result: SearchMemoryResult): Promise<void> {
  const md = [
    `# ${result.title}`,
    '',
    `**Type:** ${result.memory_type}`,
    `**Severity:** ${result.severity || 'N/A'}`,
    '',
    '## Summary',
    result.summary,
    '',
    '## Why Matched',
    result.why_matched,
  ].join('\n');

  const doc = await vscode.workspace.openTextDocument({
    language: 'markdown',
    content: md,
  });
  await vscode.window.showTextDocument(doc, { preview: true });
}
