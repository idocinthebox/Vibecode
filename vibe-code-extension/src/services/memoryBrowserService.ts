import { VibeCodeApiClient } from './apiClient';
import { MemoryItem, MemoryTreeData, TokenSavingsData } from '../types/memory';
import { getLogger } from '../ui/outputChannel';

export class MemoryBrowserService {
  constructor(private api: VibeCodeApiClient) {}

  async refresh(projectPath: string): Promise<MemoryTreeData> {
    const logger = getLogger();
    try {
      const response = await this.api.searchMemory({
        query: '',
        project_path: projectPath,
        max_results: 100,
      });

      const items: MemoryItem[] = response.results.map((r) => ({
        memoryType: r.memory_type,
        memoryId: r.memory_id,
        title: r.title,
        summary: r.summary,
        severity: r.severity,
        whyMatched: r.why_matched,
        sourceType: r.source_type,
        sourceRef: r.source_ref,
        confidenceScore: r.confidence_score,
        correctedApproach: r.corrected_approach,
      }));

      const failures = items.filter((i) => i.memoryType === 'failure_pattern');
      const rules = items.filter((i) => i.memoryType === 'project_rule');
      const successes = items.filter((i) => i.memoryType === 'success_pattern');

      // Sort failures by severity
      const severityOrder: Record<string, number> = {
        critical: 0,
        high: 1,
        medium: 2,
        low: 3,
      };
      failures.sort(
        (a, b) =>
          (severityOrder[a.severity || 'low'] ?? 4) -
          (severityOrder[b.severity || 'low'] ?? 4)
      );

      return {
        groups: [
          {
            label: `Failure Warnings (${failures.length})`,
            icon: 'warning',
            children: failures,
          },
          {
            label: `Project Rules (${rules.length})`,
            icon: 'book',
            children: rules,
          },
          {
            label: `Success Patterns (${successes.length})`,
            icon: 'check',
            children: successes,
          },
        ],
        offline: false,
      };
    } catch (err) {
      logger.error(`refresh failed: ${err}`);
      return { groups: [], offline: true };
    }
  }

  async search(query: string, projectPath: string): Promise<MemoryItem[]> {
    const response = await this.api.searchMemory({
      query,
      project_path: projectPath,
      max_results: 50,
    });
    return response.results.map((r) => ({
      memoryType: r.memory_type,
      memoryId: r.memory_id,
      title: r.title,
      summary: r.summary,
      severity: r.severity,
      whyMatched: r.why_matched,
      sourceType: r.source_type,
      sourceRef: r.source_ref,
      confidenceScore: r.confidence_score,
      correctedApproach: r.corrected_approach,
    }));
  }

  async getTokenSavings(): Promise<TokenSavingsData | null> {
    try {
      const response = await this.api.tokenReport(30);
      return {
        estimatedTokensSaved: response.estimated_tokens_saved,
        successPatterns: response.success_patterns,
        failurePatterns: response.failure_patterns,
        projectRules: response.project_rules,
        autoCapturedSuccess: response.auto_captured_success,
        autoCapturedFailure: response.auto_captured_failure,
        preventionHits: response.prevention_hits,
        estimatedTokensSavedAuto: response.estimated_tokens_saved_auto,
        days: response.days,
      };
    } catch {
      return null;
    }
  }

  buildPreviewMarkdown(item: MemoryItem): string {
    const lines = [
      `# ${item.title}`,
      '',
      `**Type:** ${item.memoryType}`,
    ];
    if (item.severity) {
      lines.push(`**Severity:** ${item.severity}`);
    }
    if (item.sourceType) {
      lines.push(`**Source:** ${item.sourceType}`);
    }
    lines.push('');
    lines.push('## Summary');
    lines.push(item.summary);
    if (item.whyMatched) {
      lines.push('');
      lines.push('## Why Matched');
      lines.push(item.whyMatched);
    }
    return lines.join('\n');
  }

  buildContextSnippet(item: MemoryItem): string {
    const lines = [`## ${item.title}`, '', item.summary];
    if (item.whyMatched) {
      lines.push('', `*Why:* ${item.whyMatched}`);
    }
    return lines.join('\n');
  }
}
