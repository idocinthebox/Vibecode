import * as vscode from 'vscode';

export interface VibeCodeDiagnosticData {
  memoryId: string;
  memoryType: string;
  severity: string;
  preventionRule?: string;
  correctedApproach?: string;
  source?: string;
}

export const VIBE_CODE_DIAGNOSTIC_SOURCE = 'vibecode';

export function createVibeCodeDiagnostic(
  range: vscode.Range,
  message: string,
  severity: vscode.DiagnosticSeverity,
  data: VibeCodeDiagnosticData
): vscode.Diagnostic {
  const diagnostic = new vscode.Diagnostic(range, message, severity);
  diagnostic.source = VIBE_CODE_DIAGNOSTIC_SOURCE;
  diagnostic.code = data.memoryId;
  (diagnostic as any).vibeCodeData = data;
  return diagnostic;
}

export function getVibeCodeData(
  diagnostic: vscode.Diagnostic
): VibeCodeDiagnosticData | undefined {
  return (diagnostic as any).vibeCodeData;
}
