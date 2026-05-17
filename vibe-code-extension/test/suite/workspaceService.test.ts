import * as assert from 'assert';
import { normalizePath, isSubPath } from '../../src/utils/pathUtils';

suite('Path Utils', () => {
  test('normalizePath converts backslashes', () => {
    const result = normalizePath('C:\\Users\\test\\file.ts');
    assert.ok(result.includes('/'));
    assert.ok(!result.includes('\\'));
  });

  test('isSubPath detects subpaths', () => {
    assert.ok(isSubPath('/home/project', '/home/project/src/main.ts'));
    assert.ok(!isSubPath('/home/project', '/other/project/main.ts'));
  });
});
