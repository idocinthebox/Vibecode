import * as vscode from 'vscode';
import * as path from 'path';
import { getLogger } from '../ui/outputChannel';

const MAX_CONTEXT_CHARS = 4000;

export class DocumentContextService {
  buildQuery(document: vscode.TextDocument, selection?: vscode.Selection): string {
    const logger = getLogger();
    const parts: string[] = [];

    // Filename and relative path
    const fileName = path.basename(document.fileName);
    parts.push(fileName);

    const workspaceFolder = vscode.workspace.getWorkspaceFolder(document.uri);
    if (workspaceFolder) {
      const relPath = path.relative(workspaceFolder.uri.fsPath, document.fileName);
      parts.push(relPath);
    }

    // Language
    parts.push(document.languageId);

    // Current line or selection
    let textContext = '';
    if (selection && !selection.isEmpty) {
      textContext = document.getText(selection);
    } else {
      const position = vscode.window.activeTextEditor?.selection.active;
      if (position) {
        const line = document.lineAt(position.line);
        textContext = line.text.trim();
        // Add a few surrounding lines for context
        const startLine = Math.max(0, position.line - 2);
        const endLine = Math.min(document.lineCount - 1, position.line + 2);
        const surrounding = [];
        for (let i = startLine; i <= endLine; i++) {
          surrounding.push(document.lineAt(i).text.trim());
        }
        textContext = surrounding.join('\n');
      }
    }

    if (textContext) {
      parts.push(textContext);
    }

    const query = parts.join(' ');

    // Hard limit
    if (query.length > MAX_CONTEXT_CHARS) {
      logger.debug(`Truncating context query from ${query.length} to ${MAX_CONTEXT_CHARS}`);
      return query.substring(0, MAX_CONTEXT_CHARS);
    }

    return query;
  }

  isSecretSensitiveFile(document: vscode.TextDocument): boolean {
    const fileName = path.basename(document.fileName).toLowerCase();
    const ext = path.extname(document.fileName).toLowerCase();

    const sensitiveNames = [
      '.env',
      '.env.local',
      '.env.production',
      '.env.development',
      'id_rsa',
      'id_dsa',
      'id_ecdsa',
      'id_ed25519',
      '.aws/credentials',
      'credentials',
      'secrets',
      'private.key',
      'key.pem',
      'cert.pem',
    ];

    const sensitiveExts = ['.key', '.pem', '.p12', '.pfx', '.crt'];

    if (sensitiveNames.some((n) => fileName.includes(n))) {
      return true;
    }

    if (sensitiveExts.includes(ext)) {
      return true;
    }

    return false;
  }
}
