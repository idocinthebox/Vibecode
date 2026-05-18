import * as assert from 'assert';
import * as fs from 'fs';
import * as path from 'path';
import { VibeCodeApiClient } from '../../src/services/apiClient';

suite('Harvest Command', () => {
  function loadPkg(): any {
    const pkgPath = path.resolve(__dirname, '../../../package.json');
    return JSON.parse(fs.readFileSync(pkgPath, 'utf-8'));
  }

  test('harvest command is contributed in package.json', () => {
    const pkg = loadPkg();
    const commands = pkg.contributes.commands.map((c: { command: string }) => c.command);
    assert.ok(commands.includes('vibeCode.harvestProjectKnowledge'));
    assert.ok(commands.includes('vibeCode.confirmHarvestedPending'));
    assert.ok(commands.includes('vibeCode.discardHarvestedPending'));
  });

  test('harvest settings are contributed in package.json', () => {
    const pkg = loadPkg();
    const props = pkg.contributes.configuration.properties;
    assert.ok(props['vibeCode.harvest.enabled']);
    assert.ok(props['vibeCode.harvest.runOnInit']);
    assert.ok(props['vibeCode.harvest.autoConfirmThreshold']);
    assert.ok(props['vibeCode.harvest.maxFiles']);
    assert.ok(props['vibeCode.harvest.sources']);
  });

  test('api client exposes harvest methods', () => {
    const client = new VibeCodeApiClient('http://127.0.0.1:8765');
    assert.strictEqual(typeof client.harvestScan, 'function');
    assert.strictEqual(typeof client.harvestPreview, 'function');
    assert.strictEqual(typeof client.harvestReport, 'function');
  });
});
