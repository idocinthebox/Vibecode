import * as vscode from 'vscode';
import { VibeCodeApiClient } from '../services/apiClient';

export function registerShareToDatabankCommand(
  context: vscode.ExtensionContext,
  api: VibeCodeApiClient,
  workspace: typeof vscode.workspace,
): void {
  const disposable = vscode.commands.registerCommand(
    'vibeCode.shareToDatabank',
    async () => {
      const memoryType = await vscode.window.showQuickPick(
        ['failure_pattern', 'success_pattern', 'project_rule'],
        {
          placeHolder: 'Select memory type to share',
          title: 'Share to Pro Databank',
        },
      );
      if (!memoryType) {
        return;
      }

      const memoryId = await vscode.window.showInputBox({
        prompt: 'Enter the memory ID to share',
        placeHolder: 'e.g. 550e8400-e29b-41d4-a716-446655440000',
        validateInput: (v) => (v.trim() ? undefined : 'Memory ID cannot be empty'),
      });
      if (!memoryId) {
        return;
      }

      try {
        const result = await api.shareToDatabank({
          memory_type: memoryType as 'failure_pattern' | 'success_pattern' | 'project_rule',
          memory_id: memoryId.trim(),
        });
        if (result.ok) {
          vscode.window.showInformationMessage(
            `Shared to Pro databank. Submission ID: ${result.submission_id} (${result.review_state})`,
          );
        } else {
          vscode.window.showWarningMessage('Share succeeded but returned ok=false. Check Pro logs.');
        }
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : String(err);
        vscode.window.showErrorMessage(`Failed to share to databank: ${msg}`);
      }
    },
  );

  context.subscriptions.push(disposable);
}
