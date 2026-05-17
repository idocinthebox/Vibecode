export interface VibeCodeConfig {
  enabled: boolean;
  connectionMode: 'localService';
  localServiceUrl: string;
  defaultAgentProfile: string;
  maxInjectedTokens: number;
  includeFailureWarnings: boolean;
  projectRootMode: 'workspace' | 'gitRoot' | 'manual';
  manualProjectRoot: string;
  showTokenSavings: boolean;
  autoCaptureEnabled: boolean;
  autoCaptureFailureWindowSec: number;
  autoCaptureSuccessWindowSec: number;
  autoCaptureMinConfidence: number;
  autoCaptureRequireReview: boolean;
  autoCorrectEnabled: boolean;
}
