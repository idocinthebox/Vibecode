import * as assert from 'assert';
import * as fs from 'fs';
import * as path from 'path';

suite('Command Registration', () => {
  function loadPkg(): any {
    const pkgPath = path.resolve(__dirname, '../../../package.json');
    return JSON.parse(fs.readFileSync(pkgPath, 'utf-8'));
  }

  test('all expected commands are defined in package.json', () => {
    const pkg = loadPkg();
    const commands = pkg.contributes.commands.map((c: { command: string }) => c.command);

    assert.ok(commands.includes('vibeCode.searchMemory'));
    assert.ok(commands.includes('vibeCode.injectContext'));
    assert.ok(commands.includes('vibeCode.captureSuccess'));
    assert.ok(commands.includes('vibeCode.captureFailure'));
    assert.ok(commands.includes('vibeCode.serviceStatus'));
    assert.ok(commands.includes('vibeCode.openSettings'));
  });

  test('activation events are lazy', () => {
    const pkg = loadPkg();
    const events = pkg.activationEvents as string[];

    assert.ok(!events.includes('onStartupFinished'), 'Should not activate on startup');
    assert.ok(
      events.every((e) => e.startsWith('onCommand:') || e.startsWith('onView:') || e.startsWith('onLanguage:')),
      'All activation events should be command-based, view-based, or language-based'
    );
  });

  test('editor context menu contributions exist', () => {
    const pkg = loadPkg();
    const menus = pkg.contributes.menus['editor/context'];

    assert.ok(menus.length >= 2, 'Should have at least 2 context menu items');
    assert.ok(menus.some((m: { command: string }) => m.command === 'vibeCode.captureSuccess'));
    assert.ok(menus.some((m: { command: string }) => m.command === 'vibeCode.captureFailure'));
  });
});
