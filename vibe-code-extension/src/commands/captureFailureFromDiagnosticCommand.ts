import * as vscode from 'vscode';
import { VibeCodeApiClient } from '../services/apiClient';
import { WorkspaceService } from '../services/workspaceService';
import { VibeCodeDiagnosticData } from '../types/diagnostics';
import { getLogger } from '../ui/outputChannel';
import { showError, showInfo } from '../ui/notifications';
import { showSeverityQuickPick } from '../ui/quickPickViews';

export function registerCaptureFailureFromDiagnosticCommand(
  context: vscode.ExtensionContext,
  api: VibeCodeApiClient,
  workspace: WorkspaceService
): vscode.Disposable {
  return vscode.commands.registerCommand(
    'vibeCode.captureFailureFromDiagnostic',
    async (data?: VibeCodeDiagnosticData) => {
      const logger = getLogger();
      logger.info('Command: captureFailureFromDiagnostic');

      if (!data) {
        showError(new Error('No diagnostic data provided'));
        return;
      }

      const editor = vscode.window.activeTextEditor;
      const selected = editor?.document.getText(editor.selection) || '';

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
        const language = editor?.document.languageId;
        const filePath = editor?.document.uri.fsPath;

        const response = await api.captureFailure({
          project_path: projectRoot,
          task_intent: taskIntent,
          bad_suggestion: selected || data.preventionRule || 'N/A',
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
        logger.error(`captureFailureFromDiagnostic failed: ${err}`);
        showError(err as Error);
      }
    }
  );
}
