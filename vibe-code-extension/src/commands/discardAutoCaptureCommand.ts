import * as vscode from 'vscode';
import { VibeCodeApiClient } from '../services/apiClient';
import { PendingReviewItem } from '../types/api';
import { ReviewItemNode, ReviewQueueViewProvider } from '../views/reviewQueueView';

export function registerDiscardAutoCaptureCommand(
  context: vscode.ExtensionContext,
  api: VibeCodeApiClient,
  reviewView: ReviewQueueViewProvider
): vscode.Disposable {
  return vscode.commands.registerCommand(
    'vibeCode.discardAutoCapture',
    async (payload?: PendingReviewItem | ReviewItemNode) => {
      const item = payload instanceof ReviewItemNode ? payload.item : payload;
      if (!item) {
        return;
      }
      await api.discardReview(item.memory_id, { memory_type: item.memory_type });
      reviewView.refresh();
    }
  );
}
