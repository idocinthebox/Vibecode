import * as vscode from 'vscode';
import { VibeCodeConfig } from '../types/config';

export class ConfigService {
  getConfig(): VibeCodeConfig {
    const cfg = vscode.workspace.getConfiguration('vibeCode');
    return {
      enabled: cfg.get<boolean>('enabled', true),
      connectionMode: cfg.get<'localService'>('connectionMode', 'localService'),
      localServiceUrl: cfg.get<string>('localServiceUrl', 'http://127.0.0.1:8765'),
      defaultAgentProfile: cfg.get<string>('defaultAgentProfile', 'vscode-agent'),
      maxInjectedTokens: cfg.get<number>('maxInjectedTokens', 1500),
      includeFailureWarnings: cfg.get<boolean>('includeFailureWarnings', true),
      projectRootMode: cfg.get<'workspace' | 'gitRoot' | 'manual'>('projectRootMode', 'gitRoot'),
      manualProjectRoot: cfg.get<string>('manualProjectRoot', ''),
      showTokenSavings: cfg.get<boolean>('showTokenSavings', true),
      autoCaptureEnabled: cfg.get<boolean>('autoCapture.enabled', true),
      autoCaptureFailureWindowSec: cfg.get<number>('autoCapture.failureWindowSec', 180),
      autoCaptureSuccessWindowSec: cfg.get<number>('autoCapture.successWindowSec', 120),
      autoCaptureMinConfidence: cfg.get<number>('autoCapture.minConfidence', 0.6),
      autoCaptureRequireReview: cfg.get<boolean>('autoCapture.requireReview', true),
      autoCorrectEnabled: cfg.get<boolean>('autoCorrect.enabled', true),
    };
  }

  isEnabled(): boolean {
    return vscode.workspace.getConfiguration('vibeCode').get<boolean>('enabled', true);
  }

  async openSettings(): Promise<void> {
    await vscode.commands.executeCommand(
      'workbench.action.openSettings',
      'vibeCode'
    );
  }
}
