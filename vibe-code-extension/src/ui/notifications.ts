import * as vscode from 'vscode';
import { VibeCodeError } from '../utils/errors';

export function showError(error: VibeCodeError | Error): void {
  if (error instanceof VibeCodeError) {
    vscode.window.showErrorMessage(
      `${error.message}\n\nFix:\n${error.fix}`,
      { modal: false }
    );
  } else {
    vscode.window.showErrorMessage(error.message);
  }
}

export function showInfo(message: string): void {
  vscode.window.showInformationMessage(message);
}

export function showWarning(message: string): void {
  vscode.window.showWarningMessage(message);
}
