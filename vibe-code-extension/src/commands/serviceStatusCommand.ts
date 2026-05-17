import * as vscode from 'vscode';
import { VibeCodeApiClient } from '../services/apiClient';
import { ConfigService } from '../services/configService';
import { TokenStatusService } from '../services/tokenStatusService';
import { getLogger } from '../ui/outputChannel';
import { showError, showInfo } from '../ui/notifications';

export function registerServiceStatusCommand(
  context: vscode.ExtensionContext,
  api: VibeCodeApiClient,
  config: ConfigService,
  tokenStatus: TokenStatusService
): vscode.Disposable {
  return vscode.commands.registerCommand('vibeCode.serviceStatus', async () => {
    const logger = getLogger();
    logger.info('Command: serviceStatus');

    try {
      const health = await api.health();
      tokenStatus.setReady();
      logger.info(`Service health: ${JSON.stringify(health)}`);
      showInfo(
        `VibeCode service is running.\nVersion: ${health.version}\nStorage: ${health.storage_backend}\nAllowed projects: ${health.allowed_projects_count}`
      );
    } catch (err) {
      logger.error(`serviceStatus failed: ${err}`);
      tokenStatus.setOffline();
      showError(err as Error);
    }
  });
}
