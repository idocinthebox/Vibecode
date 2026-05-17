export interface HealthResponse {
  status: string;
  version: string;
  storage_backend: string;
  database_ok: boolean;
  allowed_projects_count: number;
}

export interface SearchMemoryRequest {
  query: string;
  project_path?: string;
  language?: string;
  framework?: string;
  include_success_patterns?: boolean;
  include_failure_patterns?: boolean;
  include_project_rules?: boolean;
  max_results?: number;
}

export interface SearchMemoryResult {
  memory_type: 'success_pattern' | 'failure_pattern' | 'project_rule';
  memory_id: string;
  title: string;
  summary: string;
  why_matched: string;
  severity?: string;
  confidence_score?: number;
  source_type?: string;
  source_ref?: string;
  corrected_approach?: string;
}

export interface SearchMemoryResponse {
  query: string;
  results: SearchMemoryResult[];
  retrieval_time_ms: number;
}

export interface InjectContextRequest {
  query: string;
  project_path?: string;
  agent_profile?: string;
  max_context_tokens?: number;
  include_failure_warnings?: boolean;
  include_project_rules?: boolean;
  include_success_patterns?: boolean;
}

export interface InjectContextResponse {
  context_markdown: string;
  estimated_context_tokens: number;
  estimated_tokens_saved: number;
  included_counts: {
    failure_warnings: number;
    project_rules: number;
    success_patterns: number;
  };
  retrieval_time_ms: number;
}

export interface CaptureSuccessRequest {
  project_path: string;
  name: string;
  intent_description: string;
  language?: string;
  framework?: string;
  affected_files?: string[];
  original_prompt?: string;
  reasoning_summary?: string;
  code_before?: string;
  code_after?: string;
  diff?: string;
  explanation?: string;
  tags?: string[];
  source_type?: string;
  source_ref?: string;
  confidence?: number;
  occurrence_count?: number;
  last_seen_at?: string;
  agent_source?: string;
  review_state?: 'pending' | 'confirmed' | 'discarded';
}

export interface CaptureFailureRequest {
  project_path: string;
  task_intent: string;
  bad_suggestion: string;
  failure_reason: string;
  prevention_rule: string;
  corrected_approach?: string;
  language?: string;
  framework?: string;
  affected_files?: string[];
  severity?: string;
  tags?: string[];
  source_type?: string;
  source_ref?: string;
  confidence?: number;
  occurrence_count?: number;
  last_seen_at?: string;
  agent_source?: string;
  review_state?: 'pending' | 'confirmed' | 'discarded';
}

export interface CaptureResponse {
  pattern_id?: string;
  failure_id?: string;
  rule_id?: string;
  created: boolean;
  content_hash?: string;
}

export interface EditRange {
  start_line: number;
  start_character: number;
  end_line: number;
  end_character: number;
}

export interface ObserveEditRequest {
  event_id: string;
  project_path: string;
  file_path: string;
  language: string;
  agent_source: string;
  range: EditRange;
  text_before: string;
  text_after: string;
  timestamp: number;
  document_version: number;
}

export interface ObserveEditResponse {
  event_id: string;
}

export interface ObserveDiagnosticRequest {
  project_path: string;
  file_path: string;
  message: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  is_new: boolean;
  is_resolved: boolean;
  timestamp: number;
}

export interface ObserveTestRequest {
  project_path: string;
  status_before: 'pass' | 'fail' | 'unknown';
  status_after: 'pass' | 'fail' | 'unknown';
  test_name?: string;
  file_path?: string;
  timestamp: number;
}

export interface ObserveRevertRequest {
  project_path: string;
  event_id: string;
  reverted_to_text: string;
  timestamp: number;
}

export interface ObserveTerminalRequest {
  project_path: string;
  cwd: string;
  command: string;
  exit_code: number;
  ended_at: number;
}

export interface PendingReviewItem {
  memory_type: 'success_pattern' | 'failure_pattern';
  memory_id: string;
  title: string;
  summary: string;
  confidence: number;
  occurrence_count: number;
  review_state: 'pending' | 'confirmed' | 'discarded';
  agent_source?: string;
  last_seen_at?: string;
}

export interface ConfirmReviewRequest {
  memory_type: 'success_pattern' | 'failure_pattern';
  edits?: Record<string, unknown>;
}

export interface PreEditCheckRequest {
  project_path: string;
  file_path: string;
  language: string;
  proposed_text: string;
  task_intent?: string;
}

export interface PreEditCheckMatch {
  failure_id: string;
  prevention_rule: string;
  corrected_approach?: string;
  confidence: number;
  last_seen_at?: string;
  occurrence_count: number;
}

export interface PreEditCheckResponse {
  matches: PreEditCheckMatch[];
  estimated_tokens_saved: number;
}

export interface TokenReportResponse {
  success_patterns: number;
  failure_patterns: number;
  project_rules: number;
  estimated_tokens_saved: number;
  auto_captured_success: number;
  auto_captured_failure: number;
  prevention_hits: number;
  estimated_tokens_saved_auto: number;
  days: number;
}

export type VibeCodeErrorCode =
  | 'SERVICE_UNAVAILABLE'
  | 'PROJECT_NOT_ALLOWED'
  | 'STORAGE_NOT_INITIALIZED'
  | 'REQUEST_TIMEOUT'
  | 'INVALID_RESPONSE'
  | 'NO_SELECTION'
  | 'NO_WORKSPACE';
