import * as vscode from 'vscode';
import { VibeCodeApiClient } from '../services/apiClient';

export class AutoCaptureNotificationProvider implements vscode.Disposable {
  private readonly statusItem = vscode.window.createStatusBarItem(
    'vibeCode.autoCapture',
    vscode.StatusBarAlignment.Left,
    95
  );
  private knownPendingIds = new Set<string>();
  private refreshTimer: NodeJS.Timeout | undefined;

  constructor(private readonly api: VibeCodeApiClient) {
    this.statusItem.command = 'vibeCode.openReviewQueue';
    this.statusItem.text = '$(lightbulb) VibeCode';
    this.statusItem.tooltip = 'Open VibeCode auto-capture review queue';
    this.statusItem.show();
  }

  refreshAndNotify(): void {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
    }

    this.refreshTimer = setTimeout(async () => {
      const pending = await this.api.getPendingReview();
      const ids = new Set(pending.map((item) => `${item.memory_type}:${item.memory_id}`));
      const newItems = pending.filter((item) => !this.knownPendingIds.has(`${item.memory_type}:${item.memory_id}`));

      this.knownPendingIds = ids;
      this.statusItem.text = `$(lightbulb) VibeCode learned ${pending.length} patterns`;

      const requireReview = vscode.workspace
        .getConfiguration('vibeCode.autoCapture')
        .get<boolean>('requireReview', true);

      if (!requireReview || newItems.length === 0) {
        return;
      }

      const highConfidence = newItems.some((item) => item.confidence >= 0.8);
      if (!highConfidence) {
        return;
      }

      const choice = await vscode.window.showInformationMessage(
        `VibeCode learned ${newItems.length} new pattern(s).`,
        'Review',
        'Keep',
        'Discard'
      );

      if (choice === 'Review') {
        void vscode.commands.executeCommand('vibeCode.openReviewQueue');
      } else if (choice === 'Keep') {
        for (const item of newItems) {
          await this.api.confirmReview(item.memory_id, { memory_type: item.memory_type });
        }
      } else if (choice === 'Discard') {
        for (const item of newItems) {
          await this.api.discardReview(item.memory_id, { memory_type: item.memory_type });
        }
      }
    }, 5000);
  }

  dispose(): void {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = undefined;
    }
    this.statusItem.dispose();
  }
}
