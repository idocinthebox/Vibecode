import * as vscode from 'vscode';
import { MemoryTreeProvider } from '../views/memoryTreeProvider';
import { getLogger } from '../ui/outputChannel';

export function registerFilterMemoryCommand(
  context: vscode.ExtensionContext,
  memoryProvider: MemoryTreeProvider
): vscode.Disposable {
  return vscode.commands.registerCommand('vibeCode.filterMemory', async () => {
    const logger = getLogger();
    logger.info('Command: filterMemory');

    const query = await vscode.window.showInputBox({
      prompt: 'Filter memory items',
      placeHolder: 'Search text (empty for all)',
    });

    const typePick = await vscode.window.showQuickPick(
      [
        { label: 'All', value: 'all' as const },
        { label: 'Failure Warnings', value: 'failure' as const },
        { label: 'Project Rules', value: 'rule' as const },
        { label: 'Success Patterns', value: 'success' as const },
      ],
      { placeHolder: 'Filter by memory type' }
    );

    if (!typePick) {
      return;
    }

    memoryProvider.setFilter(query || '', typePick.value);
  });
}
