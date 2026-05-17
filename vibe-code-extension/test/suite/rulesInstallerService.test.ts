import * as assert from 'assert';
import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import { buildInstructionsBlock } from '../../src/services/rulesInstallerService';

suite('Rules Installer', () => {
  test('buildInstructionsBlock contains markers and tool names', () => {
    const block = buildInstructionsBlock();
    assert.ok(block.includes('<!-- vibecode:begin -->'));
    assert.ok(block.includes('<!-- vibecode:end -->'));
    assert.ok(block.includes('vibecode_search_memory'));
    assert.ok(block.includes('vibecode_capture_failure'));
    assert.ok(block.includes('vibecode_capture_success'));
  });

  test('block is idempotent when matched by marker', () => {
    const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'vibecode-rules-'));
    try {
      const file = path.join(tmp, 'AGENTS.md');
      const block = buildInstructionsBlock();
      fs.writeFileSync(file, 'existing content\n', 'utf-8');

      const existing = fs.readFileSync(file, 'utf-8');
      assert.ok(!existing.includes('<!-- vibecode:begin -->'));

      const merged = existing + '\n' + block;
      fs.writeFileSync(file, merged, 'utf-8');

      const after = fs.readFileSync(file, 'utf-8');
      const occurrences = (after.match(/<!-- vibecode:begin -->/g) || []).length;
      assert.strictEqual(occurrences, 1);
    } finally {
      fs.rmSync(tmp, { recursive: true, force: true });
    }
  });
});
