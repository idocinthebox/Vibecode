import * as vscode from 'vscode';
import { PendingReviewItem } from '../types/api';
import { VibeCodeApiClient } from '../services/apiClient';

export type ReviewGroupKey = 'harvested' | 'other';

export function isHarvestedPending(item: PendingReviewItem): boolean {
  return (item.source_type || '').startsWith('harvest:');
}

export class ReviewGroupNode extends vscode.TreeItem {
  constructor(
    public readonly groupKey: ReviewGroupKey,
    public readonly items: PendingReviewItem[]
  ) {
    const title = groupKey === 'harvested' ? 'Harvested (Pending)' : 'Other (Pending)';
    super(title, vscode.TreeItemCollapsibleState.Expanded);
    this.description = `${items.length}`;
    this.contextValue =
      groupKey === 'harvested' ? 'pendingReviewHarvestedGroup' : 'pendingReviewGroup';
    this.iconPath = new vscode.ThemeIcon(groupKey === 'harvested' ? 'repo' : 'list-unordered');
  }
}

export class ReviewItemNode extends vscode.TreeItem {
  constructor(
    public readonly item: PendingReviewItem,
    public readonly groupKey: ReviewGroupKey,
    checked: boolean
  ) {
    const typePrefix =
      item.memory_type === 'failure_pattern'
        ? '[F]'
        : item.memory_type === 'project_rule'
          ? '[R]'
          : '[S]';
    super(`${typePrefix} ${item.title}`, vscode.TreeItemCollapsibleState.None);

    this.description = `${item.occurrence_count} occurrences`;
    this.tooltip = `${item.summary}\nconfidence: ${item.confidence.toFixed(2)}\nsource: ${item.source_type || item.agent_source || 'unknown'}`;
    this.contextValue = 'pendingReviewItem';
    this.iconPath = this.iconForType(item.memory_type);
    this.checkboxState = checked
      ? vscode.TreeItemCheckboxState.Checked
      : vscode.TreeItemCheckboxState.Unchecked;
  }

  private iconForType(memoryType: PendingReviewItem['memory_type']): vscode.ThemeIcon {
    if (memoryType === 'failure_pattern') {
      return new vscode.ThemeIcon('warning');
    }
    if (memoryType === 'project_rule') {
      return new vscode.ThemeIcon('shield');
    }
    return new vscode.ThemeIcon('check');
  }
}

export class ReviewQueueViewProvider implements vscode.TreeDataProvider<vscode.TreeItem> {
  private readonly emitter = new vscode.EventEmitter<vscode.TreeItem | undefined | void>();
  readonly onDidChangeTreeData = this.emitter.event;
  private readonly checkedIds = new Set<string>();
  private readonly pendingById = new Map<string, PendingReviewItem>();
  private readonly groups = new Map<ReviewGroupKey, PendingReviewItem[]>();

  constructor(private readonly api: VibeCodeApiClient) {}

  refresh(): void {
    this.emitter.fire();
  }

  getTreeItem(element: vscode.TreeItem): vscode.TreeItem {
    return element;
  }

  async getChildren(element?: vscode.TreeItem): Promise<vscode.TreeItem[]> {
    if (element instanceof ReviewGroupNode) {
      return element.items.map(
        (item) => new ReviewItemNode(item, element.groupKey, this.checkedIds.has(item.memory_id))
      );
    }

    if (element instanceof ReviewItemNode) {
      return [];
    }

    try {
      const pending = await this.api.getPendingReview();
      this.rebuildCache(pending);
      if (pending.length === 0) {
        return [new vscode.TreeItem('No pending auto-captures', vscode.TreeItemCollapsibleState.None)];
      }

      const root: vscode.TreeItem[] = [];
      const harvested = this.groups.get('harvested') || [];
      const other = this.groups.get('other') || [];
      if (harvested.length > 0) {
        root.push(new ReviewGroupNode('harvested', harvested));
      }
      if (other.length > 0) {
        root.push(new ReviewGroupNode('other', other));
      }

      return root;
    } catch {
      return [new vscode.TreeItem('Review queue unavailable', vscode.TreeItemCollapsibleState.None)];
    }
  }

  updateCheckedState(changes: ReadonlyArray<[vscode.TreeItem, vscode.TreeItemCheckboxState]>): void {
    for (const [treeItem, state] of changes) {
      if (!(treeItem instanceof ReviewItemNode)) {
        continue;
      }
      if (state === vscode.TreeItemCheckboxState.Checked) {
        this.checkedIds.add(treeItem.item.memory_id);
      } else {
        this.checkedIds.delete(treeItem.item.memory_id);
      }
    }
    this.emitter.fire();
  }

  getCheckedItems(groupKey?: ReviewGroupKey): PendingReviewItem[] {
    const source = groupKey ? this.groups.get(groupKey) || [] : Array.from(this.pendingById.values());
    return source.filter((item) => this.checkedIds.has(item.memory_id));
  }

  clearChecked(groupKey?: ReviewGroupKey): void {
    if (!groupKey) {
      this.checkedIds.clear();
      return;
    }
    const groupItems = this.groups.get(groupKey) || [];
    for (const item of groupItems) {
      this.checkedIds.delete(item.memory_id);
    }
  }

  private rebuildCache(pending: PendingReviewItem[]): void {
    this.pendingById.clear();
    const harvested: PendingReviewItem[] = [];
    const other: PendingReviewItem[] = [];

    for (const item of pending) {
      this.pendingById.set(item.memory_id, item);
      if (isHarvestedPending(item)) {
        harvested.push(item);
      } else {
        other.push(item);
      }
    }

    this.groups.set('harvested', harvested);
    this.groups.set('other', other);

    const validIds = new Set(pending.map((item) => item.memory_id));
    for (const checkedId of Array.from(this.checkedIds)) {
      if (!validIds.has(checkedId)) {
        this.checkedIds.delete(checkedId);
      }
    }
  }
}
