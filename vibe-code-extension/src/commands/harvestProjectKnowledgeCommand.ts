import * as vscode from 'vscode';
import { VibeCodeApiClient } from '../services/apiClient';
import { WorkspaceService } from '../services/workspaceService';
import { HarvestCandidateItem, HarvestScanResponse } from '../types/api';
import { ReviewQueueViewProvider } from '../views/reviewQueueView';
import { showError, showInfo } from '../ui/notifications';

interface HarvestCommandOptions {
  triggeredByInit?: boolean;
}

export function registerHarvestProjectKnowledgeCommand(
  context: vscode.ExtensionContext,
  api: VibeCodeApiClient,
  workspace: WorkspaceService,
  reviewView: ReviewQueueViewProvider
): vscode.Disposable {
  return vscode.commands.registerCommand(
    'vibeCode.harvestProjectKnowledge',
    async (_options?: HarvestCommandOptions) => {
      const config = vscode.workspace.getConfiguration('vibeCode.harvest');
      const enabled = config.get<boolean>('enabled', true);
      if (!enabled) {
        showInfo('VibeCode harvest is disabled in settings.');
        return;
      }

      let projectPath = '';
      try {
        projectPath = workspace.getProjectRoot();
      } catch (err) {
        showError(err as Error);
        return;
      }

      const maxFiles = config.get<number>('maxFiles', 500);
      const autoConfirmThreshold = config.get<number>('autoConfirmThreshold', 0.8);
      const sources = config.get<string[]>('sources', []);

      let result: HarvestScanResponse;
      try {
        result = await vscode.window.withProgress(
          {
            location: vscode.ProgressLocation.Notification,
            title: 'VibeCode: Harvesting project knowledge',
            cancellable: false,
          },
          async () => {
            return api.harvestScan({
              project_path: projectPath,
              include: sources,
              max_files: maxFiles,
              auto_confirm_threshold: autoConfirmThreshold,
              dry_run: false,
            });
          }
        );
      } catch (err) {
        showError(err as Error);
        return;
      }

      reviewView.refresh();
      openHarvestSummaryWebview(context, result);
      showInfo(
        `Harvest complete: ${result.candidates} candidates, ${result.auto_confirmed} auto-confirmed, ${result.queued_for_review} queued.`
      );
    }
  );
}

function openHarvestSummaryWebview(
  context: vscode.ExtensionContext,
  result: HarvestScanResponse
): void {
  const panel = vscode.window.createWebviewPanel(
    'vibeCodeHarvestSummary',
    'VibeCode Harvest Summary',
    vscode.ViewColumn.Beside,
    {
      enableScripts: false,
      localResourceRoots: [context.extensionUri],
    }
  );

  panel.webview.html = renderSummaryHtml(result);
}

function renderSummaryHtml(result: HarvestScanResponse): string {
  const extractorRows = Object.entries(result.extractor_counts || {})
    .sort((a, b) => b[1] - a[1])
    .map(([name, count]) => `<tr><td>${escapeHtml(name)}</td><td>${count}</td></tr>`)
    .join('');

  const top = [...(result.candidate_items || [])]
    .sort((a, b) => b.confidence - a.confidence)
    .slice(0, 10);

  const topRows = top
    .map((item) => renderTopItem(item))
    .join('');

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <style>
    body { font-family: Segoe UI, Arial, sans-serif; padding: 16px; color: var(--vscode-editor-foreground); }
    h1 { font-size: 20px; margin-bottom: 8px; }
    h2 { font-size: 14px; margin-top: 20px; }
    .stats { display: grid; grid-template-columns: repeat(2, minmax(180px, 1fr)); gap: 8px; margin: 12px 0; }
    .card { background: var(--vscode-editorWidget-background); border: 1px solid var(--vscode-editorWidget-border); border-radius: 6px; padding: 10px; }
    table { width: 100%; border-collapse: collapse; }
    th, td { text-align: left; border-bottom: 1px solid var(--vscode-editorWidget-border); padding: 6px 4px; font-size: 12px; }
    code { font-family: Consolas, monospace; }
  </style>
</head>
<body>
  <h1>Harvest Summary</h1>
  <div class="stats">
    <div class="card"><strong>Scanned files:</strong> ${result.scanned_files}</div>
    <div class="card"><strong>Candidates:</strong> ${result.candidates}</div>
    <div class="card"><strong>Auto-confirmed:</strong> ${result.auto_confirmed}</div>
    <div class="card"><strong>Queued for review:</strong> ${result.queued_for_review}</div>
    <div class="card"><strong>Duplicates skipped:</strong> ${result.duplicates_skipped}</div>
    <div class="card"><strong>Report:</strong> <code>${escapeHtml(result.report_path)}</code></div>
  </div>

  <h2>Counts by Extractor</h2>
  <table>
    <thead><tr><th>Extractor</th><th>Count</th></tr></thead>
    <tbody>${extractorRows || '<tr><td colspan="2">No extractor data</td></tr>'}</tbody>
  </table>

  <h2>Top Confidence Items</h2>
  <table>
    <thead><tr><th>Type</th><th>Title</th><th>Confidence</th><th>Source</th></tr></thead>
    <tbody>${topRows || '<tr><td colspan="4">No candidates</td></tr>'}</tbody>
  </table>
</body>
</html>`;
}

function renderTopItem(item: HarvestCandidateItem): string {
  return `<tr>
    <td>${escapeHtml(item.memory_type)}</td>
    <td>${escapeHtml(item.title)}</td>
    <td>${item.confidence.toFixed(2)}</td>
    <td>${escapeHtml(item.source_ref)}</td>
  </tr>`;
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
