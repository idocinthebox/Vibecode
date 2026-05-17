import * as vscode from 'vscode';
import {
  ObserveDiagnosticRequest,
  ObserveRevertRequest,
  ObserveTerminalRequest,
  ObserveTestRequest,
} from '../types/api';
import { VibeCodeApiClient } from './apiClient';
import { EditAttributionService } from './editAttributionService';
import { WorkspaceService } from './workspaceService';
import { AutoCaptureNotificationProvider } from '../providers/autoCaptureNotificationProvider';

interface RecentEdit {
  eventId: string;
  filePath: string;
  timestampMs: number;
  textBefore: string;
  rangeStartLine: number;
  rangeStartChar: number;
  rangeEndLine: number;
  rangeEndChar: number;
}

export class OutcomeObserverService implements vscode.Disposable {
  private readonly recentEdits = new Map<string, RecentEdit[]>();
  private readonly previousDiagnostics = new Map<string, Set<string>>();
  private readonly taskStatus = new Map<string, 'pass' | 'fail' | 'unknown'>();

  constructor(
    private readonly api: VibeCodeApiClient,
    private readonly workspace: WorkspaceService,
    private readonly editAttribution: EditAttributionService,
    private readonly notifications: AutoCaptureNotificationProvider
  ) {}

  register(): vscode.Disposable[] {
    const disposables: vscode.Disposable[] = [];

    disposables.push(
      this.editAttribution.onEditObserved(async (edit) => {
        await this.api.observeEdit(edit);
        const bucket = this.recentEdits.get(edit.file_path) || [];
        bucket.push({
          eventId: edit.event_id,
          filePath: edit.file_path,
          timestampMs: edit.timestamp * 1000,
          textBefore: edit.text_before,
          rangeStartLine: edit.range.start_line,
          rangeStartChar: edit.range.start_character,
          rangeEndLine: edit.range.end_line,
          rangeEndChar: edit.range.end_character,
        });
        if (bucket.length > 25) {
          bucket.shift();
        }
        this.recentEdits.set(edit.file_path, bucket);
      })
    );

    disposables.push(
      vscode.languages.onDidChangeDiagnostics(async (event) => {
        const projectPath = this.workspace.getProjectRoot();
        for (const uri of event.uris) {
          if (uri.scheme !== 'file') {
            continue;
          }

          const key = uri.toString();
          const oldSet = this.previousDiagnostics.get(key) || new Set<string>();
          const diagnostics = vscode.languages.getDiagnostics(uri);
          const newSet = new Set<string>();

          for (const d of diagnostics) {
            const signature = `${d.source || ''}|${d.code || ''}|${d.message}`;
            newSet.add(signature);
            if (!oldSet.has(signature)) {
              const req: ObserveDiagnosticRequest = {
                project_path: projectPath,
                file_path: uri.fsPath,
                message: d.message,
                severity: this.mapSeverity(d.severity),
                is_new: true,
                is_resolved: false,
                timestamp: Date.now() / 1000,
              };
              await this.api.observeDiagnostic(req);
            }
          }

          for (const oldSig of oldSet) {
            if (!newSet.has(oldSig)) {
              const message = oldSig.split('|').slice(2).join('|');
              const req: ObserveDiagnosticRequest = {
                project_path: projectPath,
                file_path: uri.fsPath,
                message,
                severity: 'medium',
                is_new: false,
                is_resolved: true,
                timestamp: Date.now() / 1000,
              };
              await this.api.observeDiagnostic(req);
            }
          }

          this.previousDiagnostics.set(key, newSet);
        }

        this.notifications.refreshAndNotify();
      })
    );

    disposables.push(
      vscode.workspace.onDidChangeTextDocument(async (event) => {
        const filePath = event.document.uri.fsPath;
        const bucket = this.recentEdits.get(filePath);
        if (!bucket || bucket.length === 0) {
          return;
        }

        const nowMs = Date.now();
        const failureWindowSec = vscode.workspace
          .getConfiguration('vibeCode.autoCapture')
          .get<number>('failureWindowSec', 180);

        for (const change of event.contentChanges) {
          const matched = bucket.find(
            (item) =>
              nowMs - item.timestampMs <= failureWindowSec * 1000 &&
              item.rangeStartLine === change.range.start.line &&
              item.rangeStartChar === change.range.start.character &&
              item.rangeEndLine === change.range.end.line &&
              item.rangeEndChar === change.range.end.character &&
              change.text === item.textBefore
          );

          if (!matched) {
            continue;
          }

          const req: ObserveRevertRequest = {
            project_path: this.workspace.getProjectRoot(),
            event_id: matched.eventId,
            reverted_to_text: matched.textBefore,
            timestamp: Date.now() / 1000,
          };
          await this.api.observeRevert(req);
        }

        this.notifications.refreshAndNotify();
      })
    );

    disposables.push(
      vscode.tasks.onDidEndTaskProcess(async (event) => {
        const execution = event.execution;
        const taskName = execution.task.name;
        const before = this.taskStatus.get(taskName) || 'unknown';
        const code = event.exitCode ?? -1;
        const after = code === 0 ? 'pass' : 'fail';
        this.taskStatus.set(taskName, after);

        const req: ObserveTestRequest = {
          project_path: this.workspace.getProjectRoot(),
          status_before: before,
          status_after: after,
          test_name: taskName,
          timestamp: Date.now() / 1000,
        };
        await this.api.observeTest(req);
        this.notifications.refreshAndNotify();
      })
    );

    const windowAny = vscode.window as unknown as {
      onDidEndTerminalShellExecution?: (
        listener: (event: { execution: { commandLine: { value: string } }; exitCode: number; terminal: vscode.Terminal }) => void
      ) => vscode.Disposable;
    };

    if (typeof windowAny.onDidEndTerminalShellExecution === 'function') {
      disposables.push(
        windowAny.onDidEndTerminalShellExecution(async (event) => {
          const req: ObserveTerminalRequest = {
            project_path: this.workspace.getProjectRoot(),
            cwd: this.workspace.getProjectRoot(),
            command: event.execution.commandLine.value,
            exit_code: event.exitCode ?? -1,
            ended_at: Date.now() / 1000,
          };
          await this.api.observeTerminal(req);
          this.notifications.refreshAndNotify();
        })
      );
    }

    return disposables;
  }

  private mapSeverity(severity: vscode.DiagnosticSeverity): 'low' | 'medium' | 'high' | 'critical' {
    switch (severity) {
      case vscode.DiagnosticSeverity.Error:
        return 'critical';
      case vscode.DiagnosticSeverity.Warning:
        return 'high';
      case vscode.DiagnosticSeverity.Information:
        return 'medium';
      default:
        return 'low';
    }
  }

  dispose(): void {
    this.recentEdits.clear();
    this.previousDiagnostics.clear();
    this.taskStatus.clear();
  }
}
