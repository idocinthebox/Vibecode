import * as vscode from 'vscode';
import { SearchMemoryResult } from '../types/api';

export async function showSearchResultsQuickPick(
  results: SearchMemoryResult[]
): Promise<SearchMemoryResult | undefined> {
  const items: vscode.QuickPickItem[] = results.map((r) => ({
    label: `$(${getIconForType(r.memory_type)}) ${r.title}`,
    description: `[${r.memory_type}] ${r.why_matched}`,
    detail: r.summary,
  }));

  const selected = await vscode.window.showQuickPick(items, {
    placeHolder: 'Select a memory result to view details',
  });

  if (!selected) {
    return undefined;
  }

  const index = items.indexOf(selected);
  return results[index];
}

function getIconForType(type: string): string {
  switch (type) {
    case 'failure_pattern':
      return 'warning';
    case 'project_rule':
      return 'book';
    case 'success_pattern':
      return 'check';
    default:
      return 'symbol-misc';
  }
}

export async function showSeverityQuickPick(): Promise<string | undefined> {
  const items = ['low', 'medium', 'high', 'critical'].map((s) => ({
    label: s.charAt(0).toUpperCase() + s.slice(1),
  }));
  const selected = await vscode.window.showQuickPick(items, {
    placeHolder: 'Select severity',
  });
  return selected?.label.toLowerCase();
}
