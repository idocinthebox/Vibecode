// Minimal vscode mock for unit tests running outside VSCode

export enum TreeItemCollapsibleState {
  None = 0,
  Collapsed = 1,
  Expanded = 2,
}

export class TreeItem {
  iconPath: any;
  tooltip: any;
  description: any;
  contextValue: any;
  command: any;
  constructor(public label: string, public collapsibleState?: TreeItemCollapsibleState) {}
}

export class ThemeIcon {
  constructor(public id: string, public color?: any) {}
}

export class ThemeColor {
  constructor(public id: string) {}
}

export class Position {
  constructor(public line: number, public character: number) {}
  isBefore() { return false; }
  isBeforeOrEqual() { return false; }
  isAfter() { return false; }
  isAfterOrEqual() { return false; }
  compareTo() { return 0; }
}

export class Range {
  start: Position;
  end: Position;
  constructor(startLine: number, startChar: number, endLine: number, endChar: number);
  constructor(start: Position, end: Position);
  constructor(a: number | Position, b: number | Position, c?: number, d?: number) {
    if (typeof a === 'number') {
      this.start = new Position(a, b as number);
      this.end = new Position(c!, d!);
    } else {
      this.start = a;
      this.end = b as Position;
    }
  }
  contains() { return true; }
  isEmpty() { return false; }
}

export class Selection extends Range {}

export enum DiagnosticSeverity {
  Error = 0,
  Warning = 1,
  Information = 2,
  Hint = 3,
}

export class Diagnostic {
  code: any;
  source: string | undefined;
  relatedInformation: any;
  tags: any;
  data: any;
  constructor(
    public range: Range,
    public message: string,
    public severity?: DiagnosticSeverity
  ) {}
}

export class MarkdownString {
  value: string;
  isTrusted: any;
  supportHtml: any;
  constructor(value?: string) { this.value = value || ''; }
  appendText(text: string) { this.value += text; return this; }
  appendMarkdown(text: string) { this.value += text; return this; }
  appendCodeblock(code: string, language?: string) { this.value += '```' + (language || '') + '\n' + code + '\n```'; return this; }
}

export class Hover {
  constructor(public contents: MarkdownString | string | any, public range?: Range) {}
}

export enum CodeActionKind {
  Empty = '',
  QuickFix = 'quickfix',
  Refactor = 'refactor',
  Source = 'source',
}

export class CodeAction {
  isPreferred?: boolean;
  disabled?: any;
  edit?: any;
  diagnostics?: Diagnostic[];
  kind?: CodeActionKind;
  constructor(public title: string, kind?: CodeActionKind) {
    this.kind = kind;
  }
}

export const window = {
  createOutputChannel: () => ({
    appendLine: () => {},
    show: () => {},
    dispose: () => {},
  }),
  createTreeView: () => ({ dispose: () => {} }),
  showTextDocument: async () => ({}),
  showInformationMessage: async () => {},
  showErrorMessage: async () => {},
  showWarningMessage: async () => {},
  showInputBox: async () => undefined,
  showQuickPick: async () => undefined,
  activeTextEditor: undefined,
  onDidChangeActiveTextEditor: () => ({ dispose: () => {} }),
};

export const workspace = {
  openTextDocument: async () => ({}),
  getConfiguration: () => ({
    get: (key: string, defaultValue: any) => defaultValue,
    update: async () => {},
  }),
  workspaceFolders: undefined,
  onDidChangeWorkspaceFolders: () => ({ dispose: () => {} }),
  onDidSaveTextDocument: () => ({ dispose: () => {} }),
  onDidCloseTextDocument: () => ({ dispose: () => {} }),
};

export const commands = {
  registerCommand: () => ({ dispose: () => {} }),
  executeCommand: async () => {},
};

export const StatusBarAlignment = { Left: 0, Right: 1 };

export const env = {
  clipboard: {
    writeText: async () => {},
  },
};

export const Uri = {
  file: (path: string) => ({ fsPath: path, scheme: 'file', path }),
};

export const EventEmitter = class EventEmitter<T> {
  event: any = () => ({ dispose: () => {} });
  fire() {}
};

export const languages = {
  createDiagnosticCollection: () => ({
    set: () => {},
    delete: () => {},
    clear: () => {},
    dispose: () => {},
    get: () => [],
    forEach: () => {},
  }),
  registerHoverProvider: () => ({ dispose: () => {} }),
  registerCodeActionsProvider: () => ({ dispose: () => {} }),
  getDiagnostics: () => [],
};

export const Disposable = class Disposable {
  constructor(public callOnDispose?: () => any) {}
  dispose() { if (this.callOnDispose) this.callOnDispose(); }
};

export const ConfigurationTarget = {
  Global: 1,
  Workspace: 2,
  WorkspaceFolder: 3,
};

export const ViewColumn = {
  One: 1,
  Two: 2,
};
