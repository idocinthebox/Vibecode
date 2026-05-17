import * as crypto from 'crypto';
import * as vscode from 'vscode';
import { ObserveEditRequest } from '../types/api';
import { DocumentContextService } from './documentContextService';

const MAX_EDIT_TEXT_CHARS = 8192;
const MAX_FILE_BYTES = 1024 * 1024;

export class EditAttributionService implements vscode.Disposable {
  private readonly emitter = new vscode.EventEmitter<ObserveEditRequest>();
  private readonly textSnapshot = new Map<string, string>();
  private lastKeyboardSignalAt = 0;

  readonly onEditObserved: vscode.Event<ObserveEditRequest> = this.emitter.event;

  constructor(private readonly contextService: DocumentContextService) {}

  register(): vscode.Disposable[] {
    const disposables: vscode.Disposable[] = [];

    for (const doc of vscode.workspace.textDocuments) {
      this.textSnapshot.set(doc.uri.toString(), doc.getText());
    }

    disposables.push(
      vscode.workspace.onDidOpenTextDocument((doc) => {
        this.textSnapshot.set(doc.uri.toString(), doc.getText());
      })
    );

    disposables.push(
      vscode.workspace.onDidCloseTextDocument((doc) => {
        this.textSnapshot.delete(doc.uri.toString());
      })
    );

    disposables.push(
      vscode.window.onDidChangeTextEditorSelection((event) => {
        if (event.kind === vscode.TextEditorSelectionChangeKind.Keyboard) {
          this.lastKeyboardSignalAt = Date.now();
        }
      })
    );

    disposables.push(
      vscode.workspace.onDidChangeTextDocument((event) => {
        this.handleChange(event);
      })
    );

    return disposables;
  }

  private handleChange(event: vscode.TextDocumentChangeEvent): void {
    const document = event.document;
    const uri = document.uri.toString();

    if (document.uri.scheme !== 'file') {
      this.textSnapshot.set(uri, document.getText());
      return;
    }

    if (this.contextService.isSecretSensitiveFile(document)) {
      this.textSnapshot.set(uri, document.getText());
      return;
    }

    if (document.getText().length > MAX_FILE_BYTES) {
      this.textSnapshot.set(uri, document.getText());
      return;
    }

    if (event.contentChanges.length === 0) {
      this.textSnapshot.set(uri, document.getText());
      return;
    }

    const previousText = this.textSnapshot.get(uri) ?? '';
    const now = Date.now();

    for (const change of event.contentChanges) {
      const before = previousText.slice(change.rangeOffset, change.rangeOffset + change.rangeLength);
      const after = change.text;
      const agentSource = this.classifySource(after, now);

      const payload: ObserveEditRequest = {
        event_id: crypto.randomUUID(),
        project_path: vscode.workspace.getWorkspaceFolder(document.uri)?.uri.fsPath || '',
        file_path: document.uri.fsPath,
        language: document.languageId,
        agent_source: agentSource,
        range: {
          start_line: change.range.start.line,
          start_character: change.range.start.character,
          end_line: change.range.end.line,
          end_character: change.range.end.character,
        },
        text_before: this.trimMiddle(before),
        text_after: this.trimMiddle(after),
        timestamp: now / 1000,
        document_version: document.version,
      };

      this.emitter.fire(payload);
    }

    this.textSnapshot.set(uri, document.getText());
  }

  private classifySource(insertedText: string, now: number): string {
    const recentKeyboard = now - this.lastKeyboardSignalAt <= 250;
    if (recentKeyboard) {
      return 'human';
    }

    const cfg = vscode.workspace.getConfiguration('vibeCode');
    const extensionIds = cfg.get<string[]>('attribution.agentExtensionIds', [
      'GitHub.copilot',
      'GitHub.copilot-chat',
      'openai.openai-codex',
      'openai.chatgpt',
      'anysphere.cursorpyright',
      'Cursor.cursor',
      'google.antigravity',
      'anthropic.claude-code',
    ]);

    for (const id of extensionIds) {
      const ext = vscode.extensions.getExtension(id);
      if (ext?.isActive) {
        return `agent:${id}`;
      }
    }

    if (insertedText.length > 40) {
      const clipboard = vscode.env.clipboard.readText();
      void clipboard;
      return 'paste';
    }

    return 'unknown';
  }

  private trimMiddle(value: string): string {
    if (value.length <= MAX_EDIT_TEXT_CHARS) {
      return value;
    }
    const half = Math.floor(MAX_EDIT_TEXT_CHARS / 2);
    return `${value.slice(0, half)}\n/* ...truncated... */\n${value.slice(value.length - half)}`;
  }

  dispose(): void {
    this.textSnapshot.clear();
    this.emitter.dispose();
  }
}
