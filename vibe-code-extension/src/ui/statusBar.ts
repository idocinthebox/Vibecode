import * as vscode from 'vscode';
import { getLogger } from './outputChannel';

export class StatusBarManager {
  private statusBarItem: vscode.StatusBarItem;

  constructor() {
    this.statusBarItem = vscode.window.createStatusBarItem(
      vscode.StatusBarAlignment.Right,
      100
    );
    this.statusBarItem.command = 'vibeCode.serviceStatus';
    this.setReady();
    this.statusBarItem.show();
  }

  setReady(): void {
    this.statusBarItem.text = '$(pass) VibeCode';
    this.statusBarItem.tooltip = 'VibeCode: Ready';
    this.statusBarItem.backgroundColor = undefined;
  }

  setOffline(): void {
    this.statusBarItem.text = '$(debug-disconnect) VibeCode';
    this.statusBarItem.tooltip = 'VibeCode: Offline\nClick to check status';
    this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
  }

  setTokenSavings(tokensSaved: number): void {
    const k = (tokensSaved / 1000).toFixed(1);
    this.statusBarItem.text = `$(pass) VibeCode: ~${k}k tokens saved`;
    this.statusBarItem.tooltip = `VibeCode: ~${tokensSaved} tokens saved`;
    this.statusBarItem.backgroundColor = undefined;
  }

  dispose(): void {
    this.statusBarItem.dispose();
  }
}
