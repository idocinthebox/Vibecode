import * as assert from 'assert';
import * as vscode from 'vscode';
import { registerShareToDatabankCommand } from '../../src/commands/shareToDatabankCommand';

suite('Pro Share Command', () => {
  test('shares selected recent item to databank', async () => {
    const calls: Array<{ memory_type: string; memory_id: string; project_path?: string }> = [];
    const api = {
      async recentMemory(): Promise<{ items: Array<{ memory_id: string; title: string; source_type?: string }>; total: number }> {
        return {
          items: [{ memory_id: 'rule-123', title: 'Always run tests', source_type: 'harvest:claude_md' }],
          total: 1,
        };
      },
      async shareToDatabank(request: { memory_type: string; memory_id: string; project_path?: string }): Promise<{ ok: boolean; submission_id: string; review_state: 'pending' | 'approved' | 'rejected' }> {
        calls.push(request);
        return { ok: true, submission_id: 'sub-1', review_state: 'pending' };
      },
    };

    const quickPickValues: Array<any> = [
      'project_rule',
      { label: 'Always run tests', description: 'rule-123', memoryId: 'rule-123' },
    ];

    const originalShowQuickPick = vscode.window.showQuickPick;
    const originalShowInformationMessage = vscode.window.showInformationMessage;
    const originalRegister = vscode.commands.registerCommand;

    let registered: (() => Promise<void>) | undefined;
    (vscode.window as any).showQuickPick = async () => quickPickValues.shift();
    (vscode.window as any).showInformationMessage = async () => undefined;
    (vscode.commands as any).registerCommand = (_id: string, callback: any) => {
      registered = callback;
      return { dispose: () => {} };
    };

    const context = { subscriptions: [] as vscode.Disposable[] } as unknown as vscode.ExtensionContext;
    const workspaceStub = {
      workspaceFolders: [{ uri: { fsPath: 'D:/Vibecoder' } }],
    } as unknown as typeof vscode.workspace;

    try {
      registerShareToDatabankCommand(context, api as any, workspaceStub);
      assert.ok(registered);
      await registered!();
    } finally {
      (vscode.window as any).showQuickPick = originalShowQuickPick;
      (vscode.window as any).showInformationMessage = originalShowInformationMessage;
      (vscode.commands as any).registerCommand = originalRegister;
    }

    assert.strictEqual(calls.length, 1);
    assert.deepStrictEqual(calls[0], {
      memory_type: 'project_rule',
      memory_id: 'rule-123',
      project_path: 'D:/Vibecoder',
    });
  });

  test('does not share when memory type selection is cancelled', async () => {
    const api = {
      async recentMemory(): Promise<{ items: never[]; total: number }> {
        return { items: [], total: 0 };
      },
      async shareToDatabank(): Promise<{ ok: boolean; submission_id: string; review_state: 'pending' | 'approved' | 'rejected' }> {
        throw new Error('should not be called');
      },
    };

    const originalShowQuickPick = vscode.window.showQuickPick;
    const originalRegister = vscode.commands.registerCommand;

    let registered: (() => Promise<void>) | undefined;
    (vscode.window as any).showQuickPick = async () => undefined;
    (vscode.commands as any).registerCommand = (_id: string, callback: any) => {
      registered = callback;
      return { dispose: () => {} };
    };

    const context = { subscriptions: [] as vscode.Disposable[] } as unknown as vscode.ExtensionContext;
    const workspaceStub = { workspaceFolders: [] } as unknown as typeof vscode.workspace;

    try {
      registerShareToDatabankCommand(context, api as any, workspaceStub);
      assert.ok(registered);
      await registered!();
    } finally {
      (vscode.window as any).showQuickPick = originalShowQuickPick;
      (vscode.commands as any).registerCommand = originalRegister;
    }
  });
});
