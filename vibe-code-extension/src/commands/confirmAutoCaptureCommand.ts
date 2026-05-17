import * as vscode from 'vscode';
import { VibeCodeApiClient } from '../services/apiClient';
import { PendingReviewItem } from '../types/api';
import { ReviewQueueViewProvider } from '../views/reviewQueueView';

export function registerConfirmAutoCaptureCommand(
  context: vscode.ExtensionContext,
  api: VibeCodeApiClient,
  reviewView: ReviewQueueViewProvider
): vscode.Disposable {
  return vscode.commands.registerCommand('vibeCode.confirmAutoCapture', async (item?: PendingReviewItem) => {
    if (!item) {
      return;
    }
    await api.confirmReview(item.memory_id, { memory_type: item.memory_type });
    reviewView.refresh();
  });
}
