import * as vscode from 'vscode';
import { ConfigService } from '../services/configService';
import { getLogger } from '../ui/outputChannel';

export function registerOpenSettingsCommand(
  context: vscode.ExtensionContext,
  config: ConfigService
): vscode.Disposable {
  return vscode.commands.registerCommand('vibeCode.openSettings', async () => {
    getLogger().info('Command: openSettings');
    await config.openSettings();
  });
}
