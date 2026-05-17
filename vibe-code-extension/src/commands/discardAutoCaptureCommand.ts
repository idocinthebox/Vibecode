import * as vscode from 'vscode';
import { VibeCodeApiClient } from '../services/apiClient';
import { PendingReviewItem } from '../types/api';
import { ReviewQueueViewProvider } from '../views/reviewQueueView';

export function registerDiscardAutoCaptureCommand(
  context: vscode.ExtensionContext,
  api: VibeCodeApiClient,
  reviewView: ReviewQueueViewProvider
): vscode.Disposable {
  return vscode.commands.registerCommand('vibeCode.discardAutoCapture', async (item?: PendingReviewItem) => {
    if (!item) {
      return;
    }
    await api.discardReview(item.memory_id, { memory_type: item.memory_type });
    reviewView.refresh();
  });
}
