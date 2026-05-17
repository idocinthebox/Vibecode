import * as assert from 'assert';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import * as vscode from 'vscode';
import { SuppressionService } from '../../src/services/suppressionService';

suite('SuppressionService', () => {
  let tempDir: string;
  let vscodeDir: string;
  let suppressionsPath: string;

  setup(() => {
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'vibecode-test-'));
    vscodeDir = path.join(tempDir, '.vscode');
    fs.mkdirSync(vscodeDir, { recursive: true });
    suppressionsPath = path.join(vscodeDir, 'vibecode-suppressions.json');

    Object.defineProperty(vscode.workspace, 'workspaceFolders', {
      configurable: true,
      get: () => [{ uri: { fsPath: tempDir } }],
    });
  });

  teardown(() => {
    Object.defineProperty(vscode.workspace, 'workspaceFolders', {
      configurable: true,
      get: () => undefined,
    });
    try {
      fs.rmSync(tempDir, { recursive: true, force: true });
    } catch {}
  });

  test('suppress adds memoryId to file', () => {
    const service = new SuppressionService();
    service.suppress('abc-123', 'Not relevant');

    assert.ok(fs.existsSync(suppressionsPath));
    const data = JSON.parse(fs.readFileSync(suppressionsPath, 'utf-8'));
    assert.strictEqual(data.suppressedWarnings.length, 1);
    assert.strictEqual(data.suppressedWarnings[0].memoryId, 'abc-123');
    assert.strictEqual(data.suppressedWarnings[0].scope, 'workspace');
  });

  test('isSuppressed returns true for suppressed memory', () => {
    const service = new SuppressionService();
    service.suppress('abc-123');
    assert.ok(service.isSuppressed('abc-123'));
  });

  test('isSuppressed returns false for unknown memory', () => {
    const service = new SuppressionService();
    assert.ok(!service.isSuppressed('unknown'));
  });

  test('clearSuppressions removes file', () => {
    const service = new SuppressionService();
    service.suppress('abc-123');
    assert.ok(fs.existsSync(suppressionsPath));

    service.clearSuppressions();
    assert.ok(!fs.existsSync(suppressionsPath));
    assert.ok(!service.isSuppressed('abc-123'));
  });
});
