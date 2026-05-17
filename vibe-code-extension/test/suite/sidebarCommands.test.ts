import * as assert from 'assert';
import * as fs from 'fs';
import * as path from 'path';

suite('Sidebar Commands in package.json', () => {
  function loadPkg(): any {
    const pkgPath = path.resolve(__dirname, '../../../package.json');
    return JSON.parse(fs.readFileSync(pkgPath, 'utf-8'));
  }

  test('views container exists', () => {
    const pkg = loadPkg();
    assert.ok(pkg.contributes.viewsContainers);
    assert.ok(pkg.contributes.viewsContainers.activitybar);
    const bar = pkg.contributes.viewsContainers.activitybar;
    assert.ok(bar.some((c: any) => c.id === 'vibeCode'));
  });

  test('memory and stats views exist', () => {
    const pkg = loadPkg();
    assert.ok(pkg.contributes.views);
    assert.ok(pkg.contributes.views.vibeCode);
    const views = pkg.contributes.views.vibeCode;
    assert.ok(views.some((v: any) => v.id === 'vibeCodeMemory'));
    assert.ok(views.some((v: any) => v.id === 'vibeCodeStats'));
  });

  test('sidebar commands are registered', () => {
    const pkg = loadPkg();
    const commands = pkg.contributes.commands.map((c: any) => c.command);
    assert.ok(commands.includes('vibeCode.refreshMemory'));
    assert.ok(commands.includes('vibeCode.filterMemory'));
    assert.ok(commands.includes('vibeCode.previewMemory'));
    assert.ok(commands.includes('vibeCode.copyMemoryContext'));
  });

  test('view title menu has refresh and filter', () => {
    const pkg = loadPkg();
    const menus = pkg.contributes.menus['view/title'];
    assert.ok(menus);
    assert.ok(menus.some((m: any) => m.command === 'vibeCode.refreshMemory' && m.when === 'view == vibeCodeMemory'));
    assert.ok(menus.some((m: any) => m.command === 'vibeCode.filterMemory' && m.when === 'view == vibeCodeMemory'));
  });
});
