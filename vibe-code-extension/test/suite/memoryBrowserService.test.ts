import * as assert from 'assert';
import { createServer, Server } from 'http';
import { MemoryBrowserService } from '../../src/services/memoryBrowserService';
import { VibeCodeApiClient } from '../../src/services/apiClient';

suite('MemoryBrowserService', () => {
  let server: Server;
  let port: number;

  setup((done) => {
    server = createServer((req, res) => {
      const url = req.url || '';
      if (url === '/memory/search') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          query: '',
          results: [
            { memory_type: 'failure_pattern', memory_id: 'f1', title: 'Fail A', summary: 'Bad', severity: 'high', why_matched: 'matched' },
            { memory_type: 'failure_pattern', memory_id: 'f2', title: 'Fail B', summary: 'Worse', severity: 'critical', why_matched: 'matched' },
            { memory_type: 'project_rule', memory_id: 'r1', title: 'Rule 1', summary: 'Do X', why_matched: 'matched' },
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

  test('refresh groups failures first', async () => {
    const client = new VibeCodeApiClient(`http://127.0.0.1:${port}`);
    const service = new MemoryBrowserService(client);
    const data = await service.refresh('/project');

    assert.strictEqual(data.offline, false);
    assert.strictEqual(data.groups.length, 3);
    assert.ok(data.groups[0].label.startsWith('Failure Warnings'));
    assert.strictEqual(data.groups[0].children.length, 2);
    assert.ok(data.groups[1].label.startsWith('Project Rules'));
    assert.ok(data.groups[2].label.startsWith('Success Patterns'));
  });

  test('refresh sorts failures by severity critical first', async () => {
    const client = new VibeCodeApiClient(`http://127.0.0.1:${port}`);
    const service = new MemoryBrowserService(client);
    const data = await service.refresh('/project');

    const failures = data.groups[0].children;
    assert.strictEqual(failures[0].severity, 'critical');
    assert.strictEqual(failures[1].severity, 'high');
  });

  test('refresh returns offline on error', async () => {
    const client = new VibeCodeApiClient('http://127.0.0.1:1');
    const service = new MemoryBrowserService(client);
    const data = await service.refresh('/project');
    assert.strictEqual(data.offline, true);
    assert.strictEqual(data.groups.length, 0);
  });

  test('buildPreviewMarkdown includes title and type', () => {
    const client = new VibeCodeApiClient(`http://127.0.0.1:${port}`);
    const service = new MemoryBrowserService(client);
    const item = {
      memoryType: 'failure_pattern' as const,
      memoryId: '1',
      title: 'Test',
      summary: 'Summary text',
      severity: 'high',
      whyMatched: 'Because',
    };
    const md = service.buildPreviewMarkdown(item);
    assert.ok(md.includes('# Test'));
    assert.ok(md.includes('failure_pattern'));
    assert.ok(md.includes('Summary text'));
    assert.ok(md.includes('Because'));
  });

  test('buildContextSnippet includes title and summary', () => {
    const client = new VibeCodeApiClient(`http://127.0.0.1:${port}`);
    const service = new MemoryBrowserService(client);
    const item = {
      memoryType: 'project_rule' as const,
      memoryId: '1',
      title: 'Rule',
      summary: 'Do not do X',
    };
    const snippet = service.buildContextSnippet(item);
    assert.ok(snippet.includes('Rule'));
    assert.ok(snippet.includes('Do not do X'));
  });
});
