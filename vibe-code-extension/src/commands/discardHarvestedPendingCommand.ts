import * as vscode from 'vscode';
import { VibeCodeApiClient } from '../services/apiClient';
import { ReviewGroupNode, ReviewQueueViewProvider } from '../views/reviewQueueView';
import { showInfo } from '../ui/notifications';

export function registerDiscardHarvestedPendingCommand(
  context: vscode.ExtensionContext,
  api: VibeCodeApiClient,
  reviewView: ReviewQueueViewProvider
): vscode.Disposable {
  return vscode.commands.registerCommand(
    'vibeCode.discardHarvestedPending',
    async (group?: ReviewGroupNode) => {
      const items = reviewView.getCheckedItems(group?.groupKey || 'harvested');
      if (items.length === 0) {
        showInfo('No checked harvested items to discard.');
        return;
      }

      await Promise.all(items.map((item) => api.discardReview(item.memory_id, { memory_type: item.memory_type })));
      reviewView.clearChecked(group?.groupKey || 'harvested');
      reviewView.refresh();
      showInfo(`Discarded ${items.length} harvested item(s).`);
    }
  );
}
