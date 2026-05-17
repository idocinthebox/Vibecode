import * as assert from 'assert';
import { createServer, Server } from 'http';
import { VibeCodeApiClient } from '../../src/services/apiClient';
import { DocumentContextService } from '../../src/services/documentContextService';
import { WarningMatchService } from '../../src/services/warningMatchService';
import { SuppressionService } from '../../src/services/suppressionService';

suite('DocumentContextService', () => {
  test('isSecretSensitiveFile detects .env files', () => {
    const service = new DocumentContextService();
    assert.ok(service.isSecretSensitiveFile({ fileName: '.env', languageId: 'plaintext' } as any));
    assert.ok(service.isSecretSensitiveFile({ fileName: '.env.local', languageId: 'plaintext' } as any));
  });

  test('isSecretSensitiveFile detects key files', () => {
    const service = new DocumentContextService();
    assert.ok(service.isSecretSensitiveFile({ fileName: 'id_rsa', languageId: 'plaintext' } as any));
    assert.ok(service.isSecretSensitiveFile({ fileName: 'private.key', languageId: 'plaintext' } as any));
  });

  test('isSecretSensitiveFile returns false for normal files', () => {
    const service = new DocumentContextService();
    assert.ok(!service.isSecretSensitiveFile({ fileName: 'main.py', languageId: 'python' } as any));
    assert.ok(!service.isSecretSensitiveFile({ fileName: 'app.ts', languageId: 'typescript' } as any));
  });
});

suite('WarningMatchService', () => {
  let server: Server;
  let port: number;

  setup((done) => {
    server = createServer((req, res) => {
      const url = req.url || '';
      if (url === '/memory/search') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          query: 'test',
          results: [
            { memory_type: 'failure_pattern', memory_id: 'f1', title: 'Fail Critical', summary: 'Bad', severity: 'critical', why_matched: 'matched' },
            { memory_type: 'failure_pattern', memory_id: 'f2', title: 'Fail High', summary: 'Worse', severity: 'high', why_matched: 'matched' },
            { memory_type: 'failure_pattern', memory_id: 'f3', title: 'Fail Low', summary: 'Minor', severity: 'low', why_matched: 'matched' },
            { memory_type: 'project_rule', memory_id: 'r1', title: 'Rule 1', summary: 'Do X', severity: 'high', why_matched: 'matched' },
            { memory_type: 'success_pattern', memory_id: 's1', title: 'Success 1', summary: 'Do Y', why_matched: 'matched' },
          ],
          retrieval_time_ms: 5,
        }));
      } else {
        res.writeHead(404);
        res.end();
      }
    });
    server.listen(0, '127.0.0.1', () => {
      const addr = server.address();
      port = typeof addr === 'object' && addr ? addr.port : 8765;
      done();
    });
  });

  teardown((done) => {
    server.close(done);
  });

  test('findWarnings filters by severity', async () => {
    const client = new VibeCodeApiClient(`http://127.0.0.1:${port}`);
    const service = new WarningMatchService(client);
    const warnings = await service.findWarnings('test', '/project', 'python', 'high');

    // Should only get critical + high failures and high rules (no low)
    assert.ok(warnings.length >= 2);
    assert.ok(!warnings.some((w) => w.severity === 'low'));
  });

  test('findWarnings excludes success patterns', async () => {
    const client = new VibeCodeApiClient(`http://127.0.0.1:${port}`);
    const service = new WarningMatchService(client);
    const warnings = await service.findWarnings('test', '/project', 'python', 'low');

    // Success patterns should not be in results (only failures and rules)
    assert.ok(warnings.every((w) => (w as any).memoryType !== 'success_pattern'));
  });

  test('findWarnings sorts by severity critical first', async () => {
    const client = new VibeCodeApiClient(`http://127.0.0.1:${port}`);
    const service = new WarningMatchService(client);
    const warnings = await service.findWarnings('test', '/project', 'python', 'low');

    const severities = warnings.map((w) => w.severity);
    const criticalIndex = severities.indexOf('critical');
    const highIndex = severities.indexOf('high');
    const lowIndex = severities.indexOf('low');

    assert.ok(criticalIndex <= highIndex, 'critical should come before high');
    assert.ok(highIndex <= lowIndex, 'high should come before low');
  });

  test('findWarnings returns empty on error', async () => {
    const client = new VibeCodeApiClient('http://127.0.0.1:1');
    const service = new WarningMatchService(client);
    const warnings = await service.findWarnings('test', '/project', 'python', 'high');
    assert.deepStrictEqual(warnings, []);
  });
});
