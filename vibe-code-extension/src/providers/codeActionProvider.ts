import * as vscode from 'vscode';
import { getVibeCodeData, VIBE_CODE_DIAGNOSTIC_SOURCE } from '../types/diagnostics';

export class VibeCodeCodeActionProvider implements vscode.CodeActionProvider {
  public static readonly providedCodeActionKinds = [
    vscode.CodeActionKind.QuickFix,
  ];

  provideCodeActions(
    document: vscode.TextDocument,
    range: vscode.Range | vscode.Selection,
    context: vscode.CodeActionContext,
    token: vscode.CancellationToken
  ): vscode.CodeAction[] {
    const vibeCodeDiagnostics = context.diagnostics.filter(
      (d) => d.source === VIBE_CODE_DIAGNOSTIC_SOURCE
    );

    if (vibeCodeDiagnostics.length === 0) {
      return [];
    }

    const actions: vscode.CodeAction[] = [];

    for (const diagnostic of vibeCodeDiagnostics) {
      const data = getVibeCodeData(diagnostic);
      if (!data) {
        continue;
      }

      // Generate Agent Context
      const generateAction = new vscode.CodeAction(
        'VibeCode: Generate Agent Context for This Warning',
        vscode.CodeActionKind.QuickFix
      );
      generateAction.command = {
        command: 'vibeCode.generateContextFromDiagnostic',
        title: 'Generate Agent Context',
        arguments: [data],
      };
      generateAction.diagnostics = [diagnostic];
      actions.push(generateAction);

      // Search Related Memory
      const searchAction = new vscode.CodeAction(
        'VibeCode: Search Related Memory',
        vscode.CodeActionKind.QuickFix
      );
      searchAction.command = {
        command: 'vibeCode.searchRelatedMemory',
        title: 'Search Related Memory',
        arguments: [data],
      };
      searchAction.diagnostics = [diagnostic];
      actions.push(searchAction);

      // Capture as Failure
      const captureFailureAction = new vscode.CodeAction(
        'VibeCode: Capture as Failure Pattern',
        vscode.CodeActionKind.QuickFix
      );
      captureFailureAction.command = {
        command: 'vibeCode.captureFailureFromDiagnostic',
        title: 'Capture as Failure Pattern',
        arguments: [data],
      };
      captureFailureAction.diagnostics = [diagnostic];
      actions.push(captureFailureAction);

      if (data.correctedApproach && data.correctedApproach.trim().length > 0) {
        const applyCorrectedAction = new vscode.CodeAction(
          `VibeCode: Apply corrected approach (from failure pattern ${data.memoryId})`,
          vscode.CodeActionKind.QuickFix
        );
        const edit = new vscode.WorkspaceEdit();
        edit.replace(document.uri, diagnostic.range, data.correctedApproach);
        applyCorrectedAction.edit = edit;
        applyCorrectedAction.diagnostics = [diagnostic];
        actions.push(applyCorrectedAction);
      }

      // Ignore Warning
      const ignoreAction = new vscode.CodeAction(
        'VibeCode: Ignore This Warning in Workspace',
        vscode.CodeActionKind.QuickFix
      );
      ignoreAction.command = {
        command: 'vibeCode.ignoreWarning',
        title: 'Ignore This Warning',
        arguments: [data],
      };
      ignoreAction.diagnostics = [diagnostic];
      actions.push(ignoreAction);
    }

    return actions;
  }
}
