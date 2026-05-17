import * as vscode from 'vscode';
import { MemoryBrowserService } from '../services/memoryBrowserService';
import { MemoryItem } from '../types/memory';
import { getLogger } from '../ui/outputChannel';
import { showError } from '../ui/notifications';

export function registerPreviewMemoryCommand(
  context: vscode.ExtensionContext,
  browser: MemoryBrowserService
): vscode.Disposable {
  return vscode.commands.registerCommand(
    'vibeCode.previewMemory',
    async (item?: MemoryItem) => {
      const logger = getLogger();
      logger.info('Command: previewMemory');

      if (!item) {
        showError(new Error('No memory item selected'));
        return;
      }

      try {
        const markdown = browser.buildPreviewMarkdown(item);
        const doc = await vscode.workspace.openTextDocument({
          language: 'markdown',
          content: markdown,
        });
        await vscode.window.showTextDocument(doc, { preview: true });
      } catch (err) {
        logger.error(`previewMemory failed: ${err}`);
        showError(err as Error);
      }
    }
  );
}
