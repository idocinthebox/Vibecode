import * as assert from 'assert';
import { EditAttributionService } from '../../src/services/editAttributionService';
import { DocumentContextService } from '../../src/services/documentContextService';

suite('EditAttributionService', () => {
  test('register returns disposables and service disposes cleanly', () => {
    const service = new EditAttributionService(new DocumentContextService());
    const disposables = service.register();

    assert.ok(Array.isArray(disposables));
    assert.ok(disposables.length > 0);

    disposables.forEach((d) => d.dispose());
    service.dispose();
  });
});
