import * as assert from 'assert';
import { VibeCodeApiClient } from '../../src/services/apiClient';
import { createServer, Server } from 'http';

suite('API Client', () => {
  let server: Server;
  let port: number;

  setup((done) => {
    server = createServer((req, res) => {
      const url = req.url || '';
      if (url === '/health') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'ok', version: '0.3.0', storage_backend: 'sqlite', database_ok: true, allowed_projects_count: 0 }));
      } else if (url === '/memory/search') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ query: 'test', results: [], retrieval_time_ms: 5 }));
      } else if (url === '/memory/inject') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          context_markdown: '# Context',
          estimated_context_tokens: 100,
          estimated_tokens_saved: 50,
          included_counts: { failure_warnings: 1, project_rules: 0, success_patterns: 0 },
          retrieval_time_ms: 10,
        }));
      } else if (url === '/memory/capture-success') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ pattern_id: 'abc', created: true, content_hash: 'hash' }));
      } else if (url === '/memory/capture-failure') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ failure_id: 'def', created: true, content_hash: 'hash' }));
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

  test('health returns ok', async () => {
    const client = new VibeCodeApiClient(`http://127.0.0.1:${port}`);
    const health = await client.health();
    assert.strictEqual(health.status, 'ok');
  });

  test('searchMemory returns results', async () => {
    const client = new VibeCodeApiClient(`http://127.0.0.1:${port}`);
    const result = await client.searchMemory({ query: 'test' });
    assert.strictEqual(result.query, 'test');
    assert.deepStrictEqual(result.results, []);
  });

  test('injectContext returns markdown', async () => {
    const client = new VibeCodeApiClient(`http://127.0.0.1:${port}`);
    const result = await client.injectContext({ query: 'fix audio' });
    assert.strictEqual(result.context_markdown, '# Context');
  });
});
