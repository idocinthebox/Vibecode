import * as assert from 'assert';
import * as vscode from 'vscode';
import { registerConfirmHarvestedPendingCommand } from '../../src/commands/confirmHarvestedPendingCommand';
import { PendingReviewItem } from '../../src/types/api';
import {
  ReviewGroupNode,
  ReviewQueueViewProvider,
} from '../../src/views/reviewQueueView';

class FakeApi {
  constructor(private readonly items: PendingReviewItem[]) {}

  async getPendingReview(): Promise<PendingReviewItem[]> {
    return this.items;
  }

  async confirmReview(memoryId: string, _request: { memory_type: PendingReviewItem['memory_type'] }): Promise<{ ok: boolean }> {
    const item = this.items.find((candidate) => candidate.memory_id === memoryId);
    if (item) {
      item.review_state = 'confirmed';
    }
    return { ok: true };
  }
}

suite('Harvest Sidebar', () => {
  test('review queue groups harvested pending entries', async () => {
    const items: PendingReviewItem[] = [
      {
        memory_type: 'project_rule',
        memory_id: 'rule-1',
        title: 'Always run tests',
        summary: 'Always run tests before commit',
        confidence: 0.91,
        occurrence_count: 1,
        review_state: 'pending',
        source_type: 'harvest:claude_md',
      },
      {
        memory_type: 'failure_pattern',
        memory_id: 'failure-1',
        title: 'Shell quoting bug',
        summary: 'Use here-strings',
        confidence: 0.7,
        occurrence_count: 1,
        review_state: 'pending',
        source_type: 'auto:agent:GitHub.copilot',
      },
    ];

    const provider = new ReviewQueueViewProvider(new FakeApi(items) as any);
    const root = await provider.getChildren();

    const harvestedGroup = root.find(
      (node): node is ReviewGroupNode =>
        node instanceof ReviewGroupNode && node.groupKey === 'harvested'
    );

    assert.ok(harvestedGroup);
    const harvestedChildren = await provider.getChildren(harvestedGroup);
    assert.strictEqual(harvestedChildren.length, 1);
  });

  test('bulk confirm command confirms checked harvested items', async () => {
    const items: PendingReviewItem[] = [
      {
        memory_type: 'project_rule',
        memory_id: 'rule-1',
        title: 'Always run tests',
        summary: 'Always run tests before commit',
        confidence: 0.91,
        occurrence_count: 1,
        review_state: 'pending',
        source_type: 'harvest:claude_md',
      },
    ];

    const api = new FakeApi(items);
    const provider = new ReviewQueueViewProvider(api as any);
    const root = await provider.getChildren();
    const harvestedGroup = root.find(
      (node): node is ReviewGroupNode =>
        node instanceof ReviewGroupNode && node.groupKey === 'harvested'
    );
    assert.ok(harvestedGroup);

    const children = await provider.getChildren(harvestedGroup);
    provider.updateCheckedState([[children[0], vscode.TreeItemCheckboxState.Checked]]);

    let registered: ((group?: ReviewGroupNode) => Promise<void>) | undefined;
    const originalRegister = vscode.commands.registerCommand;
    (vscode.commands as any).registerCommand = (_id: string, callback: any) => {
      registered = callback;
      return { dispose: () => {} };
    };

    try {
      const disposable = registerConfirmHarvestedPendingCommand({} as any, api as any, provider);
      assert.ok(registered);
      await registered!(harvestedGroup);
      disposable.dispose();
    } finally {
      (vscode.commands as any).registerCommand = originalRegister;
    }

    assert.strictEqual(items[0].review_state, 'confirmed');
  });
});
