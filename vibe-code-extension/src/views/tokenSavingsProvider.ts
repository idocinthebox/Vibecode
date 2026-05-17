import * as vscode from 'vscode';
import { MemoryBrowserService } from '../services/memoryBrowserService';

export class TokenSavingsProvider
  implements vscode.TreeDataProvider<vscode.TreeItem>
{
  private _onDidChangeTreeData: vscode.EventEmitter<
    vscode.TreeItem | undefined | void
  > = new vscode.EventEmitter<vscode.TreeItem | undefined | void>();
  readonly onDidChangeTreeData: vscode.Event<vscode.TreeItem | undefined | void> =
    this._onDidChangeTreeData.event;

  constructor(private browser: MemoryBrowserService) {}

  refresh(): void {
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element: vscode.TreeItem): vscode.TreeItem {
    return element;
  }

  async getChildren(): Promise<vscode.TreeItem[]> {
    const data = await this.browser.getTokenSavings();

    if (!data) {
      const offline = new vscode.TreeItem(
        'Token report unavailable',
        vscode.TreeItemCollapsibleState.None
      );
      offline.tooltip = 'Run: vibecode service doctor';
      offline.iconPath = new vscode.ThemeIcon('info');
      return [offline];
    }

    const items: vscode.TreeItem[] = [];

    const saved = new vscode.TreeItem(
      `Tokens saved: ${data.estimatedTokensSaved}`,
      vscode.TreeItemCollapsibleState.None
    );
    saved.iconPath = new vscode.ThemeIcon('sparkle');
    items.push(saved);

    const success = new vscode.TreeItem(
      `Success patterns: ${data.successPatterns}`,
      vscode.TreeItemCollapsibleState.None
    );
    success.iconPath = new vscode.ThemeIcon('check');
    items.push(success);

    const failure = new vscode.TreeItem(
      `Failure patterns: ${data.failurePatterns}`,
      vscode.TreeItemCollapsibleState.None
    );
    failure.iconPath = new vscode.ThemeIcon('warning');
    items.push(failure);

    const rules = new vscode.TreeItem(
      `Project rules: ${data.projectRules}`,
      vscode.TreeItemCollapsibleState.None
    );
    rules.iconPath = new vscode.ThemeIcon('bookmark');
    items.push(rules);

    const days = new vscode.TreeItem(
      `Report period: ${data.days} days`,
      vscode.TreeItemCollapsibleState.None
    );
    days.iconPath = new vscode.ThemeIcon('calendar');
    items.push(days);

    if (typeof data.autoCapturedSuccess === 'number') {
      const autoSuccess = new vscode.TreeItem(
        `Auto-captured success: ${data.autoCapturedSuccess}`,
        vscode.TreeItemCollapsibleState.None
      );
      autoSuccess.iconPath = new vscode.ThemeIcon('rocket');
      items.push(autoSuccess);
    }

    if (typeof data.autoCapturedFailure === 'number') {
      const autoFailure = new vscode.TreeItem(
        `Auto-captured failure: ${data.autoCapturedFailure}`,
        vscode.TreeItemCollapsibleState.None
      );
      autoFailure.iconPath = new vscode.ThemeIcon('warning');
      items.push(autoFailure);
    }

    if (typeof data.preventionHits === 'number') {
      const preventionHits = new vscode.TreeItem(
        `Prevention hits: ${data.preventionHits}`,
        vscode.TreeItemCollapsibleState.None
      );
      preventionHits.iconPath = new vscode.ThemeIcon('shield');
      items.push(preventionHits);
    }

    return items;
  }
}
