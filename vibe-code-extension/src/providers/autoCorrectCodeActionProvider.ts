import * as vscode from 'vscode';
import { getVibeCodeData, VIBE_CODE_DIAGNOSTIC_SOURCE } from '../types/diagnostics';

export class AutoCorrectCodeActionProvider implements vscode.CodeActionProvider {
  static readonly providedCodeActionKinds = [vscode.CodeActionKind.QuickFix];

  provideCodeActions(
    document: vscode.TextDocument,
    _range: vscode.Range | vscode.Selection,
    context: vscode.CodeActionContext
  ): vscode.CodeAction[] {
    const actions: vscode.CodeAction[] = [];
    for (const diagnostic of context.diagnostics) {
      if (diagnostic.source !== VIBE_CODE_DIAGNOSTIC_SOURCE) {
        continue;
      }

      const data = getVibeCodeData(diagnostic);
      if (!data?.correctedApproach) {
        continue;
      }

      const action = new vscode.CodeAction(
        `VibeCode: Apply corrected approach (from failure pattern ${data.memoryId})`,
        vscode.CodeActionKind.QuickFix
      );
      const edit = new vscode.WorkspaceEdit();
      edit.replace(document.uri, diagnostic.range, data.correctedApproach);
      action.edit = edit;
      action.diagnostics = [diagnostic];
      actions.push(action);
    }

    return actions;
  }
}
