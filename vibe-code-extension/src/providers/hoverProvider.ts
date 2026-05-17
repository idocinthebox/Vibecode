import * as vscode from 'vscode';
import { getVibeCodeData } from '../types/diagnostics';

export class VibeCodeHoverProvider implements vscode.HoverProvider {
  provideHover(
    document: vscode.TextDocument,
    position: vscode.Position,
    token: vscode.CancellationToken
  ): vscode.ProviderResult<vscode.Hover> {
    const diagnostics = vscode.languages.getDiagnostics(document.uri);
    const vibeCodeDiagnostics = diagnostics.filter(
      (d) => d.source === 'vibecode'
    );

    if (vibeCodeDiagnostics.length === 0) {
      return undefined;
    }

    // Find the closest diagnostic
    const closest = vibeCodeDiagnostics[0];
    const data = getVibeCodeData(closest);
    if (!data) {
      return undefined;
    }

    const lines: string[] = [
      `**VibeCode ${data.memoryType === 'failure_pattern' ? 'Failure Warning' : 'Project Rule'}**`,
      '',
      `**Severity:** ${data.severity}`,
    ];

    if (data.preventionRule) {
      lines.push('');
      lines.push('**Prevention Rule:**');
      lines.push(data.preventionRule);
    }

    lines.push('');
    lines.push('**Actions:**');
    lines.push('- Generate Agent Context');
    lines.push('- Search VibeCode Memory');
    lines.push('- Ignore Warning');

    return new vscode.Hover(new vscode.MarkdownString(lines.join('\n')));
  }
}
