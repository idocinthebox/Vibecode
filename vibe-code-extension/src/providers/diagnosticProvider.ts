import * as vscode from 'vscode';
import { DocumentContextService } from '../services/documentContextService';
import { WarningMatchService } from '../services/warningMatchService';
import { SuppressionService } from '../services/suppressionService';
import { WorkspaceService } from '../services/workspaceService';
import { ConfigService } from '../services/configService';
import { createVibeCodeDiagnostic, VibeCodeDiagnosticData } from '../types/diagnostics';
import { getLogger } from '../ui/outputChannel';

export class VibeCodeDiagnosticProvider implements vscode.Disposable {
  private diagnosticCollection: vscode.DiagnosticCollection;
  private debounceTimer: NodeJS.Timeout | undefined;
  private activeRequests: Map<string, AbortController> = new Map();
  private lastCheckedVersion: Map<string, number> = new Map();

  constructor(
    private contextService: DocumentContextService,
    private warningService: WarningMatchService,
    private suppressionService: SuppressionService,
    private workspaceService: WorkspaceService,
    private configService: ConfigService
  ) {
    this.diagnosticCollection = vscode.languages.createDiagnosticCollection('vibecode');
  }

  register(): vscode.Disposable[] {
    const disposables: vscode.Disposable[] = [];
    const config = this.configService.getConfig();

    disposables.push(
      vscode.workspace.onDidOpenTextDocument((doc) => {
        if (config.includeFailureWarnings) {
          this.scheduleCheck(doc);
        }
      })
    );

    disposables.push(
      vscode.workspace.onDidSaveTextDocument((doc) => {
        if (config.includeFailureWarnings) {
          this.scheduleCheck(doc);
        }
      })
    );

    disposables.push(
      vscode.window.onDidChangeActiveTextEditor((editor) => {
        if (editor && config.includeFailureWarnings) {
          this.scheduleCheck(editor.document);
        }
      })
    );

    // Check already open documents
    if (config.includeFailureWarnings) {
      vscode.workspace.textDocuments.forEach((doc) => this.scheduleCheck(doc));
    }

    return disposables;
  }

  private scheduleCheck(document: vscode.TextDocument): void {
    const settings = vscode.workspace.getConfiguration('vibeCode.inlineWarnings');
    const enabled = settings.get<boolean>('enabled', true);
    if (!enabled) {
      return;
    }

    const debounceMs = settings.get<number>('debounceMs', 1500);
    const maxDiagnostics = settings.get<number>('maxDiagnostics', 5);

    if (this.contextService.isSecretSensitiveFile(document)) {
      getLogger().debug(`Skipping secret-sensitive file: ${document.fileName}`);
      return;
    }

    // Cancel existing timer
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
    }

    // Cancel existing request for this document
    const docKey = document.uri.toString();
    const existing = this.activeRequests.get(docKey);
    if (existing) {
      existing.abort();
      this.activeRequests.delete(docKey);
    }

    this.debounceTimer = setTimeout(() => {
      this.checkDocument(document, maxDiagnostics);
    }, debounceMs);
  }

  private async checkDocument(
    document: vscode.TextDocument,
    maxDiagnostics: number
  ): Promise<void> {
    const docKey = document.uri.toString();

    // Skip if version already checked
    const lastVersion = this.lastCheckedVersion.get(docKey);
    if (lastVersion === document.version) {
      return;
    }

    const controller = new AbortController();
    this.activeRequests.set(docKey, controller);

    try {
      const query = this.contextService.buildQuery(document);
      const projectPath = this.workspaceService.getProjectRoot();
      const language = document.languageId;

      const settings = vscode.workspace.getConfiguration('vibeCode.inlineWarnings');
      const minSeverity = settings.get<string>('minSeverity', 'high');

      const warnings = await this.warningService.findWarnings(
        query,
        projectPath,
        language,
        minSeverity
      );

      if (controller.signal.aborted) {
        return;
      }

      const diagnostics: vscode.Diagnostic[] = [];

      for (const warning of warnings) {
        if (this.suppressionService.isSuppressed(warning.memoryId)) {
          continue;
        }

        if (diagnostics.length >= maxDiagnostics) {
          break;
        }

        const severity = this.mapSeverity(warning.severity);
        const message = `VibeCode warning: ${warning.title}`;
        const range = new vscode.Range(0, 0, 0, 0);

        const data: VibeCodeDiagnosticData = {
          memoryId: warning.memoryId,
          memoryType: warning.memoryType,
          severity: warning.severity,
          preventionRule: warning.preventionRule,
          correctedApproach: warning.correctedApproach,
          source: warning.sourceType,
        };

        diagnostics.push(createVibeCodeDiagnostic(range, message, severity, data));
      }

      this.diagnosticCollection.set(document.uri, diagnostics);
      this.lastCheckedVersion.set(docKey, document.version);
    } catch (err) {
      getLogger().error(`Diagnostic check failed: ${err}`);
    } finally {
      this.activeRequests.delete(docKey);
    }
  }

  private mapSeverity(severity: string): vscode.DiagnosticSeverity {
    switch (severity.toLowerCase()) {
      case 'critical':
        return vscode.DiagnosticSeverity.Error;
      case 'high':
        return vscode.DiagnosticSeverity.Warning;
      case 'medium':
        return vscode.DiagnosticSeverity.Information;
      case 'low':
      default:
        return vscode.DiagnosticSeverity.Hint;
    }
  }

  dispose(): void {
    this.diagnosticCollection.dispose();
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
    }
    for (const controller of this.activeRequests.values()) {
      controller.abort();
    }
    this.activeRequests.clear();
  }
}
