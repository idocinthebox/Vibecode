import * as vscode from 'vscode';

export class Logger {
  private channel: vscode.OutputChannel;

  constructor(channelName: string = 'VibeCode') {
    this.channel = vscode.window.createOutputChannel(channelName);
  }

  info(message: string): void {
    this.channel.appendLine(`[INFO] ${message}`);
  }

  warn(message: string): void {
    this.channel.appendLine(`[WARN] ${message}`);
  }

  error(message: string): void {
    this.channel.appendLine(`[ERROR] ${message}`);
  }

  debug(message: string): void {
    const config = vscode.workspace.getConfiguration('vibeCode');
    if (config.get<boolean>('debug', false)) {
      this.channel.appendLine(`[DEBUG] ${message}`);
    }
  }

  show(): void {
    this.channel.show();
  }

  dispose(): void {
    this.channel.dispose();
  }
}
