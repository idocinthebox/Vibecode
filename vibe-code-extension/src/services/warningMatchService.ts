import { VibeCodeApiClient } from './apiClient';
import { WarningMatch } from '../types/warning';
import { getLogger } from '../ui/outputChannel';

export class WarningMatchService {
  constructor(private api: VibeCodeApiClient) {}

  async findWarnings(
    query: string,
    projectPath: string,
    language?: string,
    minSeverity: string = 'high'
  ): Promise<WarningMatch[]> {
    const logger = getLogger();

    try {
      const response = await this.api.searchMemory({
        query,
        project_path: projectPath,
        language,
        include_success_patterns: false,
        include_failure_patterns: true,
        include_project_rules: true,
        max_results: 25,
      });

      const severityRank: Record<string, number> = {
        critical: 0,
        high: 1,
        medium: 2,
        low: 3,
      };
      const minRank = severityRank[minSeverity] ?? 1;

      const matches: WarningMatch[] = [];

      for (const r of response.results) {
        const rank = severityRank[r.severity || 'low'] ?? 4;
        if (rank > minRank) {
          continue;
        }

        if (r.memory_type === 'failure_pattern') {
          matches.push({
            memoryId: r.memory_id,
            memoryType: 'failure_pattern',
            title: r.title,
            summary: r.summary,
            severity: r.severity || 'medium',
            preventionRule: r.summary,
            whyMatched: r.why_matched,
            confidenceScore: r.confidence_score,
            sourceType: r.source_type,
            sourceRef: r.source_ref,
            correctedApproach: r.corrected_approach,
          });
        } else if (r.memory_type === 'project_rule') {
          matches.push({
            memoryId: r.memory_id,
            memoryType: 'project_rule',
            title: r.title,
            summary: r.summary,
            severity: r.severity || 'medium',
            whyMatched: r.why_matched,
            confidenceScore: r.confidence_score,
            sourceType: r.source_type,
            sourceRef: r.source_ref,
          });
        }
      }

      // Sort by severity
      matches.sort((a, b) => {
        const rankA = severityRank[a.severity] ?? 4;
        const rankB = severityRank[b.severity] ?? 4;
        return rankA - rankB;
      });

      return matches;
    } catch (err) {
      logger.error(`findWarnings failed: ${err}`);
      return [];
    }
  }
}
