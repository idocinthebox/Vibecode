import * as assert from 'assert';
import { TerminalRecallService } from '../../src/services/terminalRecallService';

suite('TerminalRecallService', () => {
  test('captureTail reads execution output', async () => {
    const service = new TerminalRecallService(
      { autoRecallOnError: async () => ({ query: '', total: 0, results: [] }) } as any,
      () => undefined,
      () => ({ get: () => true } as any),
    );

    const execution = {
      async *read() {
        yield 'ENOENT: file not found';
      },
    };

    const output = await (service as any)._captureTail(execution);
    assert.strictEqual(output, 'ENOENT: file not found');
  });
});
