import * as vscode from 'vscode';
import { Logger } from '../utils/logger';

let loggerInstance: Logger | null = null;

export function getLogger(): Logger {
  if (!loggerInstance) {
    loggerInstance = new Logger('VibeCode');
  }
  return loggerInstance;
}

export function resetLogger(): void {
  if (loggerInstance) {
    loggerInstance.dispose();
    loggerInstance = null;
  }
}
