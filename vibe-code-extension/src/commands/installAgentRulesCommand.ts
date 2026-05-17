import * as vscode from 'vscode';
import { RulesInstallerService } from '../services/rulesInstallerService';
import { getLogger } from '../ui/outputChannel';

export function registerInstallAgentRulesCommand(
  context: vscode.ExtensionContext,
  installer: RulesInstallerService
): vscode.Disposable {
  return vscode.commands.registerCommand('vibeCode.installAgentInstructions', async () => {
    getLogger().info('Command: installAgentInstructions');
    const results = await installer.installNow();
    const created = results.filter((r) => r.action === 'created').length;
    const appended = results.filter((r) => r.action === 'appended').length;
    const skipped = results.filter((r) => r.action === 'skipped').length;
    vscode.window.showInformationMessage(
      `VibeCode rules — created: ${created}, appended: ${appended}, skipped: ${skipped}.`
    );
  });
}
