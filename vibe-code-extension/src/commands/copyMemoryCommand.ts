import * as vscode from 'vscode';
import { MemoryBrowserService } from '../services/memoryBrowserService';
import { MemoryItem } from '../types/memory';
import { getLogger } from '../ui/outputChannel';
import { showError, showInfo } from '../ui/notifications';

export function registerCopyMemoryCommand(
  context: vscode.ExtensionContext,
  browser: MemoryBrowserService
): vscode.Disposable {
  return vscode.commands.registerCommand(
    'vibeCode.copyMemoryContext',
    async (item?: MemoryItem) => {
      const logger = getLogger();
      logger.info('Command: copyMemoryContext');

      if (!item) {
        showError(new Error('No memory item selected'));
        return;
      }

      try {
        const snippet = browser.buildContextSnippet(item);
        await vscode.env.clipboard.writeText(snippet);
        showInfo('Memory context copied to clipboard');
      } catch (err) {
        logger.error(`copyMemoryContext failed: ${err}`);
        showError(err as Error);
      }
    }
  );
}
