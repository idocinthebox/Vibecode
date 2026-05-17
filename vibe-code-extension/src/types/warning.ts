export interface WarningMatch {
  memoryId: string;
  memoryType: 'failure_pattern' | 'project_rule';
  title: string;
  summary: string;
  severity: string;
  preventionRule?: string;
  whyMatched: string;
  confidenceScore?: number;
  sourceType?: string;
  sourceRef?: string;
  correctedApproach?: string;
}

export interface SuppressionEntry {
  memoryId: string;
  scope: 'workspace';
  reason?: string;
  createdAt: string;
}

export interface SuppressionsFile {
  suppressedWarnings: SuppressionEntry[];
}
