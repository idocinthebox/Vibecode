import * as assert from 'assert';
import { VibeCodeCodeActionProvider } from '../../src/providers/codeActionProvider';
import { VIBE_CODE_DIAGNOSTIC_SOURCE, createVibeCodeDiagnostic } from '../../src/types/diagnostics';

suite('CodeActionProvider', () => {
  test('provides actions for vibecode diagnostics', () => {
    const provider = new VibeCodeCodeActionProvider();

    const diagnostic = createVibeCodeDiagnostic(
      { start: { line: 0, character: 0 }, end: { line: 0, character: 0 } } as any,
      'Test warning',
      1 as any,
      {
        memoryId: 'abc',
        memoryType: 'failure_pattern',
        severity: 'high',
        preventionRule: 'Do not do X',
      }
    );

    const actions = provider.provideCodeActions(
      {} as any,
      {} as any,
      { diagnostics: [diagnostic] } as any,
      {} as any
    );

    assert.ok(actions.length > 0);
    const titles = actions.map((a) => a.title);
    assert.ok(titles.some((t) => t.includes('Generate Agent Context')));
    assert.ok(titles.some((t) => t.includes('Search Related Memory')));
    assert.ok(titles.some((t) => t.includes('Capture as Failure')));
    assert.ok(titles.some((t) => t.includes('Ignore')));
  });

  test('returns empty for non-vibecode diagnostics', () => {
    const provider = new VibeCodeCodeActionProvider();

    const diagnostic = new (require('../../test/vscodeMock').TreeItem)('');
    const realDiagnostic = {
      source: 'other',
      message: 'Other error',
      range: { start: { line: 0, character: 0 }, end: { line: 0, character: 0 } },
      severity: 0,
    };

    const actions = provider.provideCodeActions(
      {} as any,
      {} as any,
      { diagnostics: [realDiagnostic] } as any,
      {} as any
    );

    assert.deepStrictEqual(actions, []);
  });
});
