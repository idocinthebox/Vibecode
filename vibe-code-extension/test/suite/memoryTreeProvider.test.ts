import * as assert from 'assert';
import { MemoryGroupItem, MemoryLeafItem, OfflineItem, EmptyItem } from '../../src/views/memoryTreeItems';
import { MemoryItem } from '../../src/types/memory';

suite('MemoryTreeItems', () => {
  test('MemoryGroupItem stores children', () => {
    const children: MemoryItem[] = [
      {
        memoryType: 'failure_pattern',
        memoryId: '1',
        title: 'Test Failure',
        summary: 'Summary',
        severity: 'high',
      },
    ];
    const item = new MemoryGroupItem('Failures', 'warning', children, 2 as any);
    assert.strictEqual(item.children.length, 1);
    assert.strictEqual(item.label, 'Failures');
  });

  test('MemoryLeafItem formats severity in label', () => {
    const memory: MemoryItem = {
      memoryType: 'failure_pattern',
      memoryId: '1',
      title: 'Bad pattern',
      summary: 'It broke',
      severity: 'critical',
    };
    const leaf = new MemoryLeafItem(memory);
    assert.ok((leaf.label as string).includes('CRITICAL'));
    assert.ok((leaf.label as string).includes('Bad pattern'));
  });

  test('MemoryLeafItem without severity shows just title', () => {
    const memory: MemoryItem = {
      memoryType: 'success_pattern',
      memoryId: '2',
      title: 'Good pattern',
      summary: 'It worked',
    };
    const leaf = new MemoryLeafItem(memory);
    assert.strictEqual(leaf.label, 'Good pattern');
  });

  test('OfflineItem has correct label', () => {
    const item = new OfflineItem();
    assert.ok((item.label as string).includes('offline'));
  });

  test('EmptyItem has default message', () => {
    const item = new EmptyItem();
    assert.ok((item.label as string).includes('No memory'));
  });
});
