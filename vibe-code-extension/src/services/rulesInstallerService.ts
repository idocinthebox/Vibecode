import * as fs from 'fs';
import * as path from 'path';
import * as vscode from 'vscode';
import { getLogger } from '../ui/outputChannel';
import { WorkspaceService } from './workspaceService';

/**
 * Installs VibeCode usage instructions into agent rule files in the workspace
 * (Copilot, Claude, Cursor, Windsurf, AGENTS.md). Idempotent: the injected
 * block is delimited by HTML comment markers and is only written if absent.
 */

const BLOCK_BEGIN = '<!-- vibecode:begin -->';
const BLOCK_END = '<!-- vibecode:end -->';
const PROMPT_STATE_KEY = 'vibeCode.rulesInstallPromptShown.v1';

export type RulesTarget = 'copilot' | 'claude' | 'cursor' | 'windsurf' | 'agents';

export interface RulesTargetDescriptor {
  id: RulesTarget;
  label: string;
  relativePath: string;
  commentStyle: 'md';
}

export const RULES_TARGETS: Record<RulesTarget, RulesTargetDescriptor> = {
  copilot: {
    id: 'copilot',
    label: 'GitHub Copilot',
    relativePath: path.join('.github', 'copilot-instructions.md'),
    commentStyle: 'md',
  },
  claude: {
    id: 'claude',
    label: 'Claude Code',
    relativePath: 'CLAUDE.md',
    commentStyle: 'md',
  },
  cursor: {
    id: 'cursor',
    label: 'Cursor',
    relativePath: path.join('.cursor', 'rules', 'vibecode.md'),
    commentStyle: 'md',
  },
  windsurf: {
    id: 'windsurf',
    label: 'Windsurf',
    relativePath: '.windsurfrules',
    commentStyle: 'md',
  },
  agents: {
    id: 'agents',
    label: 'AGENTS.md (Codex / Antigravity)',
    relativePath: 'AGENTS.md',
    commentStyle: 'md',
  },
};

const INSTRUCTIONS_BODY = `## VibeCode Agent Instructions

This workspace uses **VibeCode** — a local AI coding memory service that records
success and failure patterns to prevent repeated mistakes and reduce token waste.

When working in this workspace you MUST use the VibeCode MCP tools (exposed by
the local service at http://127.0.0.1:8765 and via MCP stdio):

1. **Before any non-trivial edit** — MUST call \`vibecode_inject_context\` (or
  \`vibecode_search_memory\`) with the task intent and target file. Read the
  returned failure warnings, project rules, and success patterns before
  proposing code.
2. **On build/test failure** — call \`vibecode_capture_failure\` with the same
   \`task_intent\` you used to inject context, plus the failing diff, the error
   output, and the affected files.
3. **On build/test success after a fix** — call \`vibecode_capture_success\`
   with the same \`task_intent\` so the win is correlated with the prior
   failure.
4. **At the end of a multi-step task or build phase** — write a short report to
   \`Docs/reports/\` summarising what changed, commit hashes, test results, and
   any follow-ups.
5. **Never** publish patterns to the shared/Pro databank automatically — that
   action is reserved for the human operator.

If the local service is unreachable, continue normally but log a one-line note
so the user can start it with \`vibecode service start\`.
`;

export function buildInstructionsBlock(): string {
  return `${BLOCK_BEGIN}\n${INSTRUCTIONS_BODY}${BLOCK_END}\n`;
}

export interface InstallResult {
  target: RulesTarget;
  filePath: string;
  action: 'created' | 'appended' | 'skipped';
  reason?: string;
}

export class RulesInstallerService {
  constructor(
    private readonly workspace: WorkspaceService,
    private readonly context: vscode.ExtensionContext
  ) {}

  /**
   * Called from extension activation. Honors the
   * `vibeCode.agentInstructions.autoInstall` setting:
   *   - "prompt" (default): show a one-time prompt per workspace.
   *   - "always": install on every activation (idempotent).
   *   - "never": no-op.
   */
  async maybeInstallOnActivation(): Promise<void> {
    const cfg = vscode.workspace.getConfiguration('vibeCode.agentInstructions');
    const mode = cfg.get<'prompt' | 'always' | 'never'>('autoInstall', 'prompt');
    const logger = getLogger();

    if (mode === 'never') {
      logger.info('Rules installer: autoInstall=never; skipping.');
      return;
    }

    if (mode === 'always') {
      await this.installSelectedTargets();
      return;
    }

    // prompt-once per workspace
    const alreadyAsked = this.context.workspaceState.get<boolean>(PROMPT_STATE_KEY, false);
    if (alreadyAsked) {
      return;
    }

    const choice = await vscode.window.showInformationMessage(
      'VibeCode can add usage instructions to your AI agent rule files (Copilot, Claude, Cursor, etc.) so agents automatically call VibeCode tools. Install them now?',
      { modal: false },
      'Install',
      'Not now',
      "Don't ask again"
    );

    await this.context.workspaceState.update(PROMPT_STATE_KEY, true);

    if (choice === 'Install') {
      await this.installSelectedTargets();
    } else if (choice === "Don't ask again") {
      await cfg.update('autoInstall', 'never', vscode.ConfigurationTarget.Workspace);
      vscode.window.showInformationMessage(
        'VibeCode: auto-install disabled for this workspace. Run "VibeCode: Install Agent Instructions" any time to add them later.'
      );
    }
  }

  /** Public entry point for the manual command. */
  async installNow(): Promise<InstallResult[]> {
    return this.installSelectedTargets();
  }

  private async installSelectedTargets(): Promise<InstallResult[]> {
    const cfg = vscode.workspace.getConfiguration('vibeCode.agentInstructions');
    const targets = cfg.get<RulesTarget[]>('targets', [
      'copilot',
      'claude',
      'cursor',
      'windsurf',
      'agents',
    ]);

    let root: string;
    try {
      root = this.workspace.getWorkspaceRoot();
    } catch {
      getLogger().warn('Rules installer: no workspace folder; skipping.');
      return [];
    }

    const results: InstallResult[] = [];
    for (const id of targets) {
      const descriptor = RULES_TARGETS[id];
      if (!descriptor) {
        continue;
      }
      try {
        results.push(this.writeOne(root, descriptor));
      } catch (err) {
        getLogger().warn(`Rules installer: failed to write ${descriptor.relativePath}: ${err}`);
        results.push({
          target: id,
          filePath: path.join(root, descriptor.relativePath),
          action: 'skipped',
          reason: String(err),
        });
      }
    }

    const written = results.filter((r) => r.action !== 'skipped');
    if (written.length > 0) {
      vscode.window.showInformationMessage(
        `VibeCode: agent instructions installed in ${written.length} file(s).`
      );
    }
    return results;
  }

  private writeOne(root: string, descriptor: RulesTargetDescriptor): InstallResult {
    const filePath = path.join(root, descriptor.relativePath);
    const block = buildInstructionsBlock();

    if (!fs.existsSync(filePath)) {
      fs.mkdirSync(path.dirname(filePath), { recursive: true });
      fs.writeFileSync(filePath, block, 'utf-8');
      getLogger().info(`Rules installer: created ${descriptor.relativePath}`);
      return { target: descriptor.id, filePath, action: 'created' };
    }

    const existing = fs.readFileSync(filePath, 'utf-8');
    if (existing.includes(BLOCK_BEGIN)) {
      return {
        target: descriptor.id,
        filePath,
        action: 'skipped',
        reason: 'VibeCode block already present',
      };
    }

    // Backup once, then append.
    const backup = `${filePath}.bak`;
    if (!fs.existsSync(backup)) {
      fs.copyFileSync(filePath, backup);
    }

    const separator = existing.endsWith('\n') ? '\n' : '\n\n';
    fs.writeFileSync(filePath, existing + separator + block, 'utf-8');
    getLogger().info(`Rules installer: appended to ${descriptor.relativePath}`);
    return { target: descriptor.id, filePath, action: 'appended' };
  }
}
