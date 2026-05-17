import { StatusBarManager } from '../ui/statusBar';

export class TokenStatusService {
  private statusBar: StatusBarManager;

  constructor(statusBar: StatusBarManager) {
    this.statusBar = statusBar;
  }

  reportSavings(tokensSaved: number): void {
    if (tokensSaved > 0) {
      this.statusBar.setTokenSavings(tokensSaved);
    } else {
      this.statusBar.setReady();
    }
  }

  setOffline(): void {
    this.statusBar.setOffline();
  }

  setReady(): void {
    this.statusBar.setReady();
  }
}
