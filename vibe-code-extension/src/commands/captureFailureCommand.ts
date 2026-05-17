import * as vscode from 'vscode';
import { VibeCodeApiClient } from '../services/apiClient';
import { WorkspaceService } from '../services/workspaceService';
import { ConfigService } from '../services/configService';
import { getLogger } from '../ui/outputChannel';
import { showError, showInfo } from '../ui/notifications';
import { showSeverityQuickPick } from '../ui/quickPickViews';

export function registerCaptureFailureCommand(
  context: vscode.ExtensionContext,
  api: VibeCodeApiClient,
  workspace: WorkspaceService,
  config: ConfigService
): vscode.Disposable {
  return vscode.commands.registerCommand('vibeCode.captureFailure', async () => {
    const logger = getLogger();
    logger.info('Command: captureFailure');

    if (!config.isEnabled()) {
      showInfo('VibeCode is disabled. Enable it in settings.');
      return;
    }

    let badSuggestion = workspace.getSelectedText();
    if (!badSuggestion) {
      badSuggestion =
        (await vscode.window.showInputBox({
          prompt: 'Bad suggestion or code that failed',
        })) || '';
    }
    if (!badSuggestion) {
      return;
    }

    const taskIntent = await vscode.window.showInputBox({
      prompt: 'Task intent',
      placeHolder: 'What were you trying to do?',
    });
    if (!taskIntent) {
      return;
    }

    const failureReason = await vscode.window.showInputBox({
      prompt: 'Why it failed',
      placeHolder: 'Explain the failure reason',
    });
    if (!failureReason) {
      return;
    }

    const preventionRule = await vscode.window.showInputBox({
      prompt: 'Prevention rule',
      placeHolder: 'Rule to prevent this in the future',
    });
    if (!preventionRule) {
      return;
    }

    const severity = await showSeverityQuickPick();
    if (!severity) {
      return;
    }

    try {
      const projectRoot = workspace.getProjectRoot();
      const language = workspace.getActiveLanguageId();
      const filePath = workspace.getActiveEditorFilePath();

      logger.info(`Capturing failure pattern: ${taskIntent}`);
      const response = await api.captureFailure({
        project_path: projectRoot,
        task_intent: taskIntent,
        bad_suggestion: badSuggestion,
        failure_reason: failureReason,
        prevention_rule: preventionRule,
        severity,
        language: language || undefined,
        affected_files: filePath ? [filePath] : undefined,
        source_type: 'vscode',
      });

      if (response.created) {
        showInfo(`Failure pattern captured: ${response.failure_id}`);
      } else {
        showInfo(`Duplicate detected: ${response.failure_id}`);
      }
    } catch (err) {
      logger.error(`captureFailure failed: ${err}`);
      showError(err as Error);
    }
  });
}
