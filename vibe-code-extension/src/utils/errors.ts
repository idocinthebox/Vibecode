import { VibeCodeErrorCode } from '../types/api';

export class VibeCodeError extends Error {
  public readonly code: VibeCodeErrorCode;
  public readonly fix: string;

  constructor(code: VibeCodeErrorCode, message: string, fix: string) {
    super(message);
    this.code = code;
    this.fix = fix;
    this.name = 'VibeCodeError';
  }
}

export const errorCatalog: Record<VibeCodeErrorCode, { message: string; fix: string }> = {
  SERVICE_UNAVAILABLE: {
    message: 'VibeCode service is not running.',
    fix: '1. Open a terminal.\n2. Run: vibecode service start\n3. Retry this command.',
  },
  PROJECT_NOT_ALLOWED: {
    message: 'This project is not in the VibeCode allowlist.',
    fix: 'Run: vibecode project allow <path>\nThen retry.',
  },
  STORAGE_NOT_INITIALIZED: {
    message: 'VibeCode storage is not initialized.',
    fix: 'Run: vibecode init\nThen: vibecode init-db',
  },
  REQUEST_TIMEOUT: {
    message: 'Request to VibeCode service timed out.',
    fix: 'Check that the service is running and responsive.',
  },
  INVALID_RESPONSE: {
    message: 'Received an invalid response from VibeCode service.',
    fix: 'Check service version matches extension expectations.',
  },
  NO_SELECTION: {
    message: 'No text is selected.',
    fix: 'Select some code in the editor, then retry.',
  },
  NO_WORKSPACE: {
    message: 'No workspace folder is open.',
    fix: 'Open a folder in VSCode, then retry.',
  },
};

export function createError(code: VibeCodeErrorCode): VibeCodeError {
  const entry = errorCatalog[code];
  return new VibeCodeError(code, entry.message, entry.fix);
}
