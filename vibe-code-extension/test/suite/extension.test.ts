import * as assert from 'assert';
import { VibeCodeApiClient } from '../../src/services/apiClient';

suite('Extension', () => {
  test('api client can be instantiated', () => {
    const client = new VibeCodeApiClient('http://127.0.0.1:8765');
    assert.ok(client);
  });

  test('api client has all required methods', () => {
    const client = new VibeCodeApiClient('http://127.0.0.1:8765');
    assert.strictEqual(typeof client.health, 'function');
    assert.strictEqual(typeof client.searchMemory, 'function');
    assert.strictEqual(typeof client.injectContext, 'function');
    assert.strictEqual(typeof client.captureSuccess, 'function');
    assert.strictEqual(typeof client.captureFailure, 'function');
  });
});
