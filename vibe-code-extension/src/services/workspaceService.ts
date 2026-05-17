import * as vscode from 'vscode';
import * as path from 'path';
import { createError } from '../utils/errors';
import { normalizePath } from '../utils/pathUtils';

export class WorkspaceService {
  getWorkspaceRoot(): string {
    const folders = vscode.workspace.workspaceFolders;
    if (!folders || folders.length === 0) {
      throw createError('NO_WORKSPACE');
    }
    return folders[0].uri.fsPath;
  }

  getProjectRoot(): string {
    const config = vscode.workspace.getConfiguration('vibeCode');
    const mode = config.get<string>('projectRootMode', 'gitRoot');

    if (mode === 'manual') {
      const manual = config.get<string>('manualProjectRoot', '');
      if (manual) {
        return manual;
      }
    }

    const workspaceRoot = this.getWorkspaceRoot();

    if (mode === 'gitRoot') {
      // simplistic git root detection: check for .git folder
      // In a real extension, you might use vscode.git extension API
      return workspaceRoot;
    }

    return workspaceRoot;
  }

  getActiveEditorFilePath(): string | undefined {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      return undefined;
    }
    return normalizePath(editor.document.uri.fsPath);
  }

  getSelectedText(): string | undefined {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      return undefined;
    }
    const selection = editor.selection;
    if (selection.isEmpty) {
      return undefined;
    }
    return editor.document.getText(selection);
  }

  getActiveLanguageId(): string | undefined {
    const editor = vscode.window.activeTextEditor;
    return editor?.document.languageId;
  }

  validateFileInWorkspace(filePath: string): boolean {
    try {
      const root = this.getWorkspaceRoot();
      return filePath.startsWith(normalizePath(root));
    } catch {
      return false;
    }
  }
}
