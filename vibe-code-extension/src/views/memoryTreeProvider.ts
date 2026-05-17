import * as vscode from 'vscode';
import { MemoryBrowserService } from '../services/memoryBrowserService';
import { MemoryGroupItem, MemoryLeafItem, OfflineItem, EmptyItem } from './memoryTreeItems';
import { MemoryItem } from '../types/memory';

export class MemoryTreeProvider
  implements vscode.TreeDataProvider<vscode.TreeItem>
{
  private _onDidChangeTreeData: vscode.EventEmitter<
    vscode.TreeItem | undefined | void
  > = new vscode.EventEmitter<vscode.TreeItem | undefined | void>();
  readonly onDidChangeTreeData: vscode.Event<vscode.TreeItem | undefined | void> =
    this._onDidChangeTreeData.event;

  private projectPath: string;
  private filterQuery: string = '';
  private filterType: 'all' | 'failure' | 'rule' | 'success' = 'all';

  constructor(
    private browser: MemoryBrowserService,
    projectPath: string
  ) {
    this.projectPath = projectPath;
  }

  refresh(): void {
    this._onDidChangeTreeData.fire();
  }

  setProjectPath(path: string): void {
    this.projectPath = path;
    this.refresh();
  }

  setFilter(query: string, type: 'all' | 'failure' | 'rule' | 'success'): void {
    this.filterQuery = query;
    this.filterType = type;
    this.refresh();
  }

  getTreeItem(element: vscode.TreeItem): vscode.TreeItem {
    return element;
  }

  async getChildren(element?: vscode.TreeItem): Promise<vscode.TreeItem[]> {
    if (element) {
      if (element instanceof MemoryGroupItem) {
        if (element.children.length === 0) {
          return [new EmptyItem()];
        }
        return element.children.map((m) => new MemoryLeafItem(m));
      }
      return [];
    }

    // Root level
    const data = await this.browser.refresh(this.projectPath);

    if (data.offline) {
      return [new OfflineItem()];
    }

    let groups = data.groups;

    // Apply type filter
    if (this.filterType !== 'all') {
      const typeMap: Record<string, string> = {
        failure: 'Failure Warnings',
        rule: 'Project Rules',
        success: 'Success Patterns',
      };
      const prefix = typeMap[this.filterType];
      groups = groups.filter((g) => g.label.startsWith(prefix));
    }

    // Apply text filter on children
    if (this.filterQuery) {
      const q = this.filterQuery.toLowerCase();
      groups = groups.map((g) => ({
        ...g,
        children: g.children.filter(
          (c) =>
            c.title.toLowerCase().includes(q) ||
            c.summary.toLowerCase().includes(q) ||
            (c.whyMatched && c.whyMatched.toLowerCase().includes(q))
        ),
      }));
    }

    return groups.map(
      (g) =>
        new MemoryGroupItem(
          g.label,
          g.icon,
          g.children,
          g.children.length > 0
            ? vscode.TreeItemCollapsibleState.Expanded
            : vscode.TreeItemCollapsibleState.Collapsed
        )
    );
  }
}
