import * as vscode from 'vscode';
import { VibeCodeDiagnosticData } from '../types/diagnostics';
import { getLogger } from '../ui/outputChannel';
import { showError } from '../ui/notifications';

export function registerSearchRelatedMemoryCommand(
  context: vscode.ExtensionContext
): vscode.Disposable {
  return vscode.commands.registerCommand(
    'vibeCode.searchRelatedMemory',
    async (data?: VibeCodeDiagnosticData) => {
      const logger = getLogger();
      logger.info('Command: searchRelatedMemory');

      if (!data) {
        showError(new Error('No diagnostic data provided'));
        return;
      }

      try {
        await vscode.commands.executeCommand('vibeCode.searchMemory', data.preventionRule || data.memoryId);
      } catch (err) {
        logger.error(`searchRelatedMemory failed: ${err}`);
        showError(err as Error);
      }
    }
  );
}
