import * as vscode from 'vscode';
import { PendingReviewItem } from '../types/api';
import { VibeCodeApiClient } from '../services/apiClient';

class ReviewItemNode extends vscode.TreeItem {
  constructor(public readonly item: PendingReviewItem) {
    const prefix = item.memory_type === 'failure_pattern' ? '[F]' : '[S]';
    super(`${prefix} ${item.title}`, vscode.TreeItemCollapsibleState.None);

    this.description = `${item.occurrence_count} occurrences`;
    this.tooltip = `${item.summary}\nconfidence: ${item.confidence.toFixed(2)}\nsource: ${item.agent_source || 'unknown'}`;
    this.contextValue = 'pendingReviewItem';
    this.iconPath = new vscode.ThemeIcon(item.memory_type === 'failure_pattern' ? 'warning' : 'check');
  }
}

export class ReviewQueueViewProvider implements vscode.TreeDataProvider<vscode.TreeItem> {
  private readonly emitter = new vscode.EventEmitter<vscode.TreeItem | undefined | void>();
  readonly onDidChangeTreeData = this.emitter.event;

  constructor(private readonly api: VibeCodeApiClient) {}

  refresh(): void {
    this.emitter.fire();
  }

  getTreeItem(element: vscode.TreeItem): vscode.TreeItem {
    return element;
  }

  async getChildren(element?: vscode.TreeItem): Promise<vscode.TreeItem[]> {
    if (element) {
      return [];
    }

    try {
      const pending = await this.api.getPendingReview();
      if (pending.length === 0) {
        return [new vscode.TreeItem('No pending auto-captures', vscode.TreeItemCollapsibleState.None)];
      }

      return pending.map((item) => {
        const node = new ReviewItemNode(item);
        node.command = {
          command: 'vibeCode.confirmAutoCapture',
          title: 'Confirm Auto Capture',
          arguments: [item],
        };
        return node;
      });
    } catch {
      return [new vscode.TreeItem('Review queue unavailable', vscode.TreeItemCollapsibleState.None)];
    }
  }
}
