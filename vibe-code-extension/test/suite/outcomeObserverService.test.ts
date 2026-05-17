import * as assert from 'assert';
import { OutcomeObserverService } from '../../src/services/outcomeObserverService';
import { EditAttributionService } from '../../src/services/editAttributionService';
import { DocumentContextService } from '../../src/services/documentContextService';
import { AutoCaptureNotificationProvider } from '../../src/providers/autoCaptureNotificationProvider';

suite('OutcomeObserverService', () => {
  test('register sets up listeners and dispose clears state', () => {
    const api = {
      observeEdit: async () => ({ event_id: 'x' }),
      observeDiagnostic: async () => undefined,
      observeTest: async () => undefined,
      observeRevert: async () => undefined,
      observeTerminal: async () => undefined,
      getPendingReview: async () => [],
    } as any;

    const workspace = {
      getProjectRoot: () => '/tmp/project',
    } as any;

    const attribution = new EditAttributionService(new DocumentContextService());
    const notifications = new AutoCaptureNotificationProvider(api);
    const observer = new OutcomeObserverService(api, workspace, attribution, notifications);

    const disposables = attribution.register();
    const observerDisposables = observer.register();

    assert.ok(disposables.length > 0);
    assert.ok(observerDisposables.length > 0);

    observerDisposables.forEach((d) => d.dispose());
    disposables.forEach((d) => d.dispose());

    observer.dispose();
    attribution.dispose();
    notifications.dispose();
  });
});
