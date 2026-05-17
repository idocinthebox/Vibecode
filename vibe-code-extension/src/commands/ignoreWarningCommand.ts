import * as vscode from 'vscode';
import { SuppressionService } from '../services/suppressionService';
import { VibeCodeDiagnosticData } from '../types/diagnostics';
import { getLogger } from '../ui/outputChannel';
import { showInfo, showError } from '../ui/notifications';

export function registerIgnoreWarningCommand(
  context: vscode.ExtensionContext,
  suppressionService: SuppressionService
): vscode.Disposable {
  return vscode.commands.registerCommand(
    'vibeCode.ignoreWarning',
    async (data?: VibeCodeDiagnosticData) => {
      const logger = getLogger();
      logger.info('Command: ignoreWarning');

      if (!data) {
        showError(new Error('No diagnostic data provided'));
        return;
      }

      const reason = await vscode.window.showInputBox({
        prompt: 'Reason for ignoring (optional)',
        placeHolder: 'e.g. Not relevant to current branch',
      });

      try {
        suppressionService.suppress(data.memoryId, reason || undefined);
        showInfo(`Warning ignored: ${data.memoryId}`);

        // Refresh diagnostics
        vscode.commands.executeCommand('vibeCode.refreshDiagnostics');
      } catch (err) {
        logger.error(`ignoreWarning failed: ${err}`);
        showError(err as Error);
      }
    }
  );
}
