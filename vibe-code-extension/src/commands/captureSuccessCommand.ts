import * as vscode from 'vscode';
import { VibeCodeApiClient } from '../services/apiClient';
import { WorkspaceService } from '../services/workspaceService';
import { ConfigService } from '../services/configService';
import { getLogger } from '../ui/outputChannel';
import { showError, showInfo } from '../ui/notifications';
import { createError } from '../utils/errors';

export function registerCaptureSuccessCommand(
  context: vscode.ExtensionContext,
  api: VibeCodeApiClient,
  workspace: WorkspaceService,
  config: ConfigService
): vscode.Disposable {
  return vscode.commands.registerCommand('vibeCode.captureSuccess', async () => {
    const logger = getLogger();
    logger.info('Command: captureSuccess');

    if (!config.isEnabled()) {
      showInfo('VibeCode is disabled. Enable it in settings.');
      return;
    }

    const selected = workspace.getSelectedText();
    if (!selected) {
      showError(createError('NO_SELECTION'));
      return;
    }

    const name = await vscode.window.showInputBox({
      prompt: 'Pattern name',
      placeHolder: 'e.g. "Restore page mpv preview fix"',
    });
    if (!name) {
      return;
    }

    const intent = await vscode.window.showInputBox({
      prompt: 'Intent description',
      placeHolder: 'What problem does this solve?',
    });
    if (!intent) {
      return;
    }

    try {
      const projectRoot = workspace.getProjectRoot();
      const language = workspace.getActiveLanguageId();
      const filePath = workspace.getActiveEditorFilePath();

      logger.info(`Capturing success pattern: ${name}`);
      const response = await api.captureSuccess({
        project_path: projectRoot,
        name,
        intent_description: intent,
        language: language || undefined,
        code_after: selected,
        affected_files: filePath ? [filePath] : undefined,
        source_type: 'vscode',
      });

      if (response.created) {
        showInfo(`Success pattern captured: ${response.pattern_id}`);
      } else {
        showInfo(`Duplicate detected: ${response.pattern_id}`);
      }
    } catch (err) {
      logger.error(`captureSuccess failed: ${err}`);
      showError(err as Error);
    }
  });
}
