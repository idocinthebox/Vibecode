import * as vscode from 'vscode';
import { MemoryItem } from '../types/memory';

export class MemoryGroupItem extends vscode.TreeItem {
  constructor(
    public readonly label: string,
    public readonly iconId: string,
    public readonly children: MemoryItem[],
    collapsibleState: vscode.TreeItemCollapsibleState
  ) {
    super(label, collapsibleState);
    this.iconPath = new vscode.ThemeIcon(iconId);
    this.contextValue = 'memoryGroup';
  }
}

export class MemoryLeafItem extends vscode.TreeItem {
  constructor(public readonly memory: MemoryItem) {
    const label = memory.severity
      ? `[${memory.severity.toUpperCase()}] ${memory.title}`
      : memory.title;
    super(label, vscode.TreeItemCollapsibleState.None);

    this.tooltip = memory.summary;
    this.description = memory.whyMatched || memory.sourceType || '';
    this.contextValue = 'memoryItem';

    if (memory.memoryType === 'failure_pattern') {
      this.iconPath = new vscode.ThemeIcon(
        'error',
        new vscode.ThemeColor('problemsErrorIcon.foreground')
      );
    } else if (memory.memoryType === 'project_rule') {
      this.iconPath = new vscode.ThemeIcon(
        'bookmark',
        new vscode.ThemeColor('symbolColor')
      );
    } else {
      this.iconPath = new vscode.ThemeIcon(
        'check',
        new vscode.ThemeColor('testing.iconPassed')
      );
    }

    this.command = {
      command: 'vibeCode.previewMemory',
      title: 'Preview Memory',
      arguments: [memory],
    };
  }
}

export class OfflineItem extends vscode.TreeItem {
  constructor() {
    super('VibeCode service is offline', vscode.TreeItemCollapsibleState.None);
    this.iconPath = new vscode.ThemeIcon(
      'plug',
      new vscode.ThemeColor('statusBarItem.warningForeground')
    );
    this.tooltip = 'Run: vibecode service start';
    this.command = {
      command: 'vibeCode.serviceStatus',
      title: 'Check Service Status',
    };
  }
}

export class EmptyItem extends vscode.TreeItem {
  constructor(message: string = 'No memory items found') {
    super(message, vscode.TreeItemCollapsibleState.None);
    this.iconPath = new vscode.ThemeIcon('info');
  }
}
