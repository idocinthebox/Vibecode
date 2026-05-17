import * as assert from 'assert';
import { createError, errorCatalog, VibeCodeError } from '../../src/utils/errors';

suite('Errors', () => {
  test('createError returns VibeCodeError with correct fields', () => {
    const err = createError('SERVICE_UNAVAILABLE');
    assert.ok(err instanceof VibeCodeError);
    assert.strictEqual(err.code, 'SERVICE_UNAVAILABLE');
    assert.ok(err.message.length > 0);
    assert.ok(err.fix.length > 0);
  });

  test('all error codes have catalog entries', () => {
    const codes = Object.keys(errorCatalog) as Array<keyof typeof errorCatalog>;
    assert.ok(codes.length > 0);
    for (const code of codes) {
      const err = createError(code);
      assert.strictEqual(err.code, code);
    }
  });
});
