export interface MemoryItem {
  memoryType: 'failure_pattern' | 'project_rule' | 'success_pattern';
  memoryId: string;
  title: string;
  summary: string;
  severity?: string;
  language?: string;
  ruleType?: string;
  whyMatched?: string;
  sourceType?: string;
  sourceRef?: string;
  confidenceScore?: number;
  correctedApproach?: string;
}

export interface MemoryGroup {
  label: string;
  icon: string;
  children: MemoryItem[];
}

export interface MemoryTreeData {
  groups: MemoryGroup[];
  offline: boolean;
}

export interface TokenSavingsData {
  estimatedTokensSaved: number;
  successPatterns: number;
  failurePatterns: number;
  projectRules: number;
  autoCapturedSuccess?: number;
  autoCapturedFailure?: number;
  preventionHits?: number;
  estimatedTokensSavedAuto?: number;
  days: number;
}

export interface MemoryDetail {
  memoryType: string;
  memoryId: string;
  title: string;
  summary: string;
  severity?: string;
  project?: string;
  source?: string;
  whyMatched?: string;
  preventionRule?: string;
  codeDiff?: string;
}
