import * as vscode from 'vscode';
import { VibeCodeApiClient } from '../services/apiClient';

type MemoryType = 'failure_pattern' | 'success_pattern' | 'project_rule';

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

      type PickItem = vscode.QuickPickItem & { memoryId?: string; manual?: boolean };
      const picks: PickItem[] = [];
      try {
        const recent = await api.recentMemory(memoryType, 25);
        for (const item of recent.items) {
          picks.push({
            label: item.title || item.memory_id,
            description: item.memory_id,
            detail: item.source_type || undefined,
            memoryId: item.memory_id,
          });
        }
      } catch {
        // Keep manual fallback available even if recent-memory query fails.
      }

      picks.push({
        label: 'Type ID...',
        description: 'Enter a memory ID manually',
        manual: true,
      });

      const selected = await vscode.window.showQuickPick(picks, {
        placeHolder: 'Select memory item to share',
        title: 'Share to Pro Databank',
      });
      if (!selected) {
        return;
      }

      let memoryId = selected.memoryId;
      if (selected.manual || !memoryId) {
        memoryId = await vscode.window.showInputBox({
          prompt: 'Enter the memory ID to share',
          placeHolder: 'e.g. 550e8400-e29b-41d4-a716-446655440000',
          validateInput: (v) => (v.trim() ? undefined : 'Memory ID cannot be empty'),
        });
      }
      if (!memoryId) {
        return;
      }

      const projectPath = workspace.workspaceFolders?.[0]?.uri?.fsPath;

      try {
        const result = await api.shareToDatabank({
          memory_type: memoryType as MemoryType,
          memory_id: memoryId.trim(),
          project_path: projectPath,
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
