import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { SuppressionsFile, SuppressionEntry } from '../types/warning';
import { getLogger } from '../ui/outputChannel';

const SUPPRESSIONS_FILE = '.vscode/vibecode-suppressions.json';

export class SuppressionService {
  private suppressions: Set<string> = new Set();
  private workspaceRoot: string | undefined;

  constructor() {
    this.loadSuppressions();
  }

  private getSuppressionPath(): string | undefined {
    const folders = vscode.workspace.workspaceFolders;
    if (!folders || folders.length === 0) {
      return undefined;
    }
    return path.join(folders[0].uri.fsPath, SUPPRESSIONS_FILE);
  }

  loadSuppressions(): void {
    const filePath = this.getSuppressionPath();
    if (!filePath || !fs.existsSync(filePath)) {
      this.suppressions.clear();
      return;
    }

    try {
      const data: SuppressionsFile = JSON.parse(
        fs.readFileSync(filePath, 'utf-8')
      );
      this.suppressions = new Set(
        (data.suppressedWarnings || []).map((e) => e.memoryId)
      );
    } catch (err) {
      getLogger().error(`Failed to load suppressions: ${err}`);
      this.suppressions.clear();
    }
  }

  isSuppressed(memoryId: string): boolean {
    return this.suppressions.has(memoryId);
  }

  suppress(memoryId: string, reason?: string): void {
    const filePath = this.getSuppressionPath();
    if (!filePath) {
      return;
    }

    let data: SuppressionsFile = { suppressedWarnings: [] };

    if (fs.existsSync(filePath)) {
      try {
        data = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
      } catch {
        data = { suppressedWarnings: [] };
      }
    }

    // Ensure .vscode dir exists
    const vscodeDir = path.dirname(filePath);
    if (!fs.existsSync(vscodeDir)) {
      fs.mkdirSync(vscodeDir, { recursive: true });
    }

    // Remove existing entry
    data.suppressedWarnings = data.suppressedWarnings.filter(
      (e) => e.memoryId !== memoryId
    );

    // Add new entry
    const entry: SuppressionEntry = {
      memoryId,
      scope: 'workspace',
      reason: reason || 'User suppressed',
      createdAt: new Date().toISOString(),
    };
    data.suppressedWarnings.push(entry);

    fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf-8');
    this.suppressions.add(memoryId);
    getLogger().info(`Suppressed warning: ${memoryId}`);
  }

  clearSuppressions(): void {
    const filePath = this.getSuppressionPath();
    if (filePath && fs.existsSync(filePath)) {
      try {
        fs.unlinkSync(filePath);
      } catch (err) {
        getLogger().error(`Failed to clear suppressions: ${err}`);
      }
    }
    this.suppressions.clear();
  }
}
