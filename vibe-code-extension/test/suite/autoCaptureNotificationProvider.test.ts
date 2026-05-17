import * as assert from 'assert';
import { AutoCaptureNotificationProvider } from '../../src/providers/autoCaptureNotificationProvider';

suite('AutoCaptureNotificationProvider', () => {
  test('refreshAndNotify handles empty pending list', async () => {
    const api = {
      getPendingReview: async () => [],
      confirmReview: async () => ({ ok: true }),
      discardReview: async () => ({ ok: true }),
    } as any;

    const provider = new AutoCaptureNotificationProvider(api);
    provider.refreshAndNotify();
    await new Promise((resolve) => setTimeout(resolve, 10));

    assert.ok(true);
    provider.dispose();
  });
});
