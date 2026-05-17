import * as vscode from 'vscode';
import { MemoryTreeProvider } from '../views/memoryTreeProvider';
import { TokenSavingsProvider } from '../views/tokenSavingsProvider';
import { getLogger } from '../ui/outputChannel';

export function registerRefreshMemoryCommand(
  context: vscode.ExtensionContext,
  memoryProvider: MemoryTreeProvider,
  savingsProvider: TokenSavingsProvider
): vscode.Disposable {
  return vscode.commands.registerCommand('vibeCode.refreshMemory', () => {
    getLogger().info('Command: refreshMemory');
    memoryProvider.refresh();
    savingsProvider.refresh();
  });
}
