import * as vscode from 'vscode';
import { ReviewQueueViewProvider } from '../views/reviewQueueView';

export function registerOpenReviewQueueCommand(
  context: vscode.ExtensionContext,
  reviewView: ReviewQueueViewProvider
): vscode.Disposable {
  return vscode.commands.registerCommand('vibeCode.openReviewQueue', async () => {
    reviewView.refresh();
    await vscode.commands.executeCommand('workbench.view.extension.vibeCode');
    await vscode.commands.executeCommand('vibeCodeReviewQueue.focus');
  });
}
