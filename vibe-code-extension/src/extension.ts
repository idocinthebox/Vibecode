import * as vscode from 'vscode';
import { VibeCodeApiClient } from './services/apiClient';
import { WorkspaceService } from './services/workspaceService';
import { ConfigService } from './services/configService';
import { TokenStatusService } from './services/tokenStatusService';
import { MemoryBrowserService } from './services/memoryBrowserService';
import { DocumentContextService } from './services/documentContextService';
import { WarningMatchService } from './services/warningMatchService';
import { SuppressionService } from './services/suppressionService';
import { AgentDetectionService } from './services/agentDetectionService';
import { AutoCorrectService } from './services/autoCorrectService';
import { EditAttributionService } from './services/editAttributionService';
import { OutcomeObserverService } from './services/outcomeObserverService';
import { RulesInstallerService } from './services/rulesInstallerService';
import { StatusBarManager } from './ui/statusBar';
import { getLogger, resetLogger } from './ui/outputChannel';
import { MemoryTreeProvider } from './views/memoryTreeProvider';
import { ReviewQueueViewProvider } from './views/reviewQueueView';
import { TokenSavingsProvider } from './views/tokenSavingsProvider';
import { AutoCaptureNotificationProvider } from './providers/autoCaptureNotificationProvider';
import { VibeCodeDiagnosticProvider } from './providers/diagnosticProvider';
import { VibeCodeHoverProvider } from './providers/hoverProvider';
import { VibeCodeCodeActionProvider } from './providers/codeActionProvider';
import { registerSearchMemoryCommand } from './commands/searchMemoryCommand';
import { registerInjectContextCommand } from './commands/injectContextCommand';
import { registerCaptureSuccessCommand } from './commands/captureSuccessCommand';
import { registerCaptureFailureCommand } from './commands/captureFailureCommand';
import { registerServiceStatusCommand } from './commands/serviceStatusCommand';
import { registerOpenSettingsCommand } from './commands/openSettingsCommand';
import { registerRefreshMemoryCommand } from './commands/refreshMemoryCommand';
import { registerFilterMemoryCommand } from './commands/filterMemoryCommand';
import { registerPreviewMemoryCommand } from './commands/previewMemoryCommand';
import { registerCopyMemoryCommand } from './commands/copyMemoryCommand';
import { registerIgnoreWarningCommand } from './commands/ignoreWarningCommand';
import { registerGenerateContextFromDiagnosticCommand } from './commands/generateContextFromDiagnosticCommand';
import { registerCaptureFailureFromDiagnosticCommand } from './commands/captureFailureFromDiagnosticCommand';
import { registerSearchRelatedMemoryCommand } from './commands/searchRelatedMemoryCommand';
import { registerConfirmAutoCaptureCommand } from './commands/confirmAutoCaptureCommand';
import { registerDiscardAutoCaptureCommand } from './commands/discardAutoCaptureCommand';
import { registerOpenReviewQueueCommand } from './commands/openReviewQueueCommand';
import { registerInstallAgentRulesCommand } from './commands/installAgentRulesCommand';
import { registerHarvestProjectKnowledgeCommand } from './commands/harvestProjectKnowledgeCommand';
import { registerConfirmHarvestedPendingCommand } from './commands/confirmHarvestedPendingCommand';
import { registerDiscardHarvestedPendingCommand } from './commands/discardHarvestedPendingCommand';
import { registerShareToDatabankCommand } from './commands/shareToDatabankCommand';
import { TerminalRecallService } from './services/terminalRecallService';

export function activate(context: vscode.ExtensionContext): void {
  const logger = getLogger();
  logger.info('VibeCode extension activating');

  const configService = new ConfigService();
  const config = configService.getConfig();

  if (!config.enabled) {
    logger.info('VibeCode is disabled in settings');
    return;
  }

  const api = new VibeCodeApiClient(config.localServiceUrl);
  const workspace = new WorkspaceService();
  const statusBar = new StatusBarManager();
  const tokenStatus = new TokenStatusService(statusBar);

  // Sidebar services
  let projectPath: string;
  try {
    projectPath = workspace.getProjectRoot();
  } catch {
    projectPath = '';
  }

  const browser = new MemoryBrowserService(api);
  const memoryProvider = new MemoryTreeProvider(browser, projectPath);
  const savingsProvider = new TokenSavingsProvider(browser);
  const reviewProvider = new ReviewQueueViewProvider(api);

  // Register tree views
  const memoryTreeView = vscode.window.createTreeView('vibeCodeMemory', {
    treeDataProvider: memoryProvider,
    showCollapseAll: true,
  });

  const savingsTreeView = vscode.window.createTreeView('vibeCodeStats', {
    treeDataProvider: savingsProvider,
  });

  const reviewQueueTreeView = vscode.window.createTreeView('vibeCodeReviewQueue', {
    treeDataProvider: reviewProvider,
    manageCheckboxStateManually: true,
  });

  const reviewCheckboxDisposable = reviewQueueTreeView.onDidChangeCheckboxState((event) => {
    reviewProvider.updateCheckedState(event.items);
  });

  context.subscriptions.push(reviewCheckboxDisposable);

  context.subscriptions.push(memoryTreeView, savingsTreeView, reviewQueueTreeView);

  // Inline warning services
  const documentContext = new DocumentContextService();
  const warningMatch = new WarningMatchService(api);
  const suppression = new SuppressionService();
  const autoCaptureNotifications = new AutoCaptureNotificationProvider(api);
  context.subscriptions.push(autoCaptureNotifications);

  const editAttribution = new EditAttributionService(documentContext);
  const attributionDisposables = editAttribution.register();
  attributionDisposables.forEach((d) => context.subscriptions.push(d));
  context.subscriptions.push(editAttribution);

  const outcomeObserver = new OutcomeObserverService(
    api,
    workspace,
    editAttribution,
    autoCaptureNotifications
  );
  if (config.autoCaptureEnabled) {
    const observerDisposables = outcomeObserver.register();
    observerDisposables.forEach((d) => context.subscriptions.push(d));
    context.subscriptions.push(outcomeObserver);
  }

  const agentDetection = new AgentDetectionService();
  const agentDetectionDisposables = agentDetection.register();
  agentDetectionDisposables.forEach((d) => context.subscriptions.push(d));
  context.subscriptions.push(agentDetection);

  const autoCorrect = new AutoCorrectService(
    api,
    configService,
    workspace,
    documentContext,
    agentDetection
  );
  if (config.autoCorrectEnabled) {
    const autoCorrectDisposables = autoCorrect.register();
    autoCorrectDisposables.forEach((d) => context.subscriptions.push(d));
    context.subscriptions.push(autoCorrect);
  }

  // Diagnostic provider
  const diagnosticProvider = new VibeCodeDiagnosticProvider(
    documentContext,
    warningMatch,
    suppression,
    workspace,
    configService
  );

  const inlineSettings = vscode.workspace.getConfiguration('vibeCode.inlineWarnings');
  if (inlineSettings.get<boolean>('enabled', true)) {
    const diagnosticDisposables = diagnosticProvider.register();
    diagnosticDisposables.forEach((d) => context.subscriptions.push(d));
    context.subscriptions.push(diagnosticProvider);

    // Hover provider
    const hoverProvider = vscode.languages.registerHoverProvider(
      { scheme: 'file' },
      new VibeCodeHoverProvider()
    );
    context.subscriptions.push(hoverProvider);

    // Code action provider
    const codeActionProvider = vscode.languages.registerCodeActionsProvider(
      { scheme: 'file' },
      new VibeCodeCodeActionProvider(),
      {
        providedCodeActionKinds: VibeCodeCodeActionProvider.providedCodeActionKinds,
      }
    );
    context.subscriptions.push(codeActionProvider);
  }

  // Check service health on activation
  api
    .health()
    .then(() => {
      logger.info(`Connected to VibeCode service at ${config.localServiceUrl}`);
      tokenStatus.setReady();
      memoryProvider.refresh();
      savingsProvider.refresh();
    })
    .catch(() => {
      logger.warn(`VibeCode service not available at ${config.localServiceUrl}`);
      tokenStatus.setOffline();
      memoryProvider.refresh();
    });

  // Register commands
  const disposables: vscode.Disposable[] = [
    statusBar,
    registerSearchMemoryCommand(context, api, workspace, configService),
    registerInjectContextCommand(context, api, workspace, configService, tokenStatus),
    registerCaptureSuccessCommand(context, api, workspace, configService),
    registerCaptureFailureCommand(context, api, workspace, configService),
    registerServiceStatusCommand(context, api, configService, tokenStatus),
    registerOpenSettingsCommand(context, configService),
    registerRefreshMemoryCommand(context, memoryProvider, savingsProvider),
    registerFilterMemoryCommand(context, memoryProvider),
    registerPreviewMemoryCommand(context, browser),
    registerCopyMemoryCommand(context, browser),
    registerIgnoreWarningCommand(context, suppression),
    registerGenerateContextFromDiagnosticCommand(context, api, workspace, configService, tokenStatus),
    registerCaptureFailureFromDiagnosticCommand(context, api, workspace),
    registerSearchRelatedMemoryCommand(context),
    registerConfirmAutoCaptureCommand(context, api, reviewProvider),
    registerDiscardAutoCaptureCommand(context, api, reviewProvider),
    registerConfirmHarvestedPendingCommand(context, api, reviewProvider),
    registerDiscardHarvestedPendingCommand(context, api, reviewProvider),
    registerOpenReviewQueueCommand(context, reviewProvider),
    registerHarvestProjectKnowledgeCommand(context, api, workspace, reviewProvider),
  ];

  // Phase 4: Pro databank share command
  registerShareToDatabankCommand(context, api, vscode.workspace);

  // Phase 8: Terminal auto-recall on error
  const terminalRecall = new TerminalRecallService(
    api,
    () => vscode.workspace.workspaceFolders,
    () => vscode.workspace.getConfiguration('vibeCode'),
  );
  terminalRecall.register(context);
  context.subscriptions.push(terminalRecall);

  // Agent rules installer (prompt-once per workspace by default).
  const rulesInstaller = new RulesInstallerService(workspace, context);
  disposables.push(registerInstallAgentRulesCommand(context, rulesInstaller));
  rulesInstaller.maybeInstallOnActivation().catch((err) => {
    logger.warn(`Rules installer failed: ${err}`);
  });

  maybePromptHarvestOnActivation(context).catch((err) => {
    logger.warn(`Harvest init prompt failed: ${err}`);
  });

  disposables.forEach((d) => context.subscriptions.push(d));
  logger.info('VibeCode extension activated');
}

export function deactivate(): void {
  getLogger().info('VibeCode extension deactivating');
  resetLogger();
}

async function maybePromptHarvestOnActivation(context: vscode.ExtensionContext): Promise<void> {
  const config = vscode.workspace.getConfiguration('vibeCode.harvest');
  const runOnInit = config.get<boolean>('runOnInit', true);
  if (!runOnInit) {
    return;
  }

  const promptKey = 'vibeCode.harvest.initPromptShown';
  if (context.workspaceState.get<boolean>(promptKey, false)) {
    return;
  }

  const hasSources = await workspaceHasHarvestSources();
  if (!hasSources) {
    return;
  }

  await context.workspaceState.update(promptKey, true);
  const choice = await vscode.window.showInformationMessage(
    'VibeCode found harvestable sources in this workspace. Harvest project knowledge now?',
    'Harvest Now',
    'Later',
    'Never Ask Again'
  );

  if (choice === 'Harvest Now') {
    await vscode.commands.executeCommand('vibeCode.harvestProjectKnowledge', { triggeredByInit: true });
    return;
  }

  if (choice === 'Never Ask Again') {
    await config.update('runOnInit', false, vscode.ConfigurationTarget.Workspace);
  }
}

async function workspaceHasHarvestSources(): Promise<boolean> {
  const probes = [
    '**/CLAUDE.md',
    '**/AGENTS.md',
    '**/CHANGELOG.md',
    '**/*.adr.md',
    '**/docs/adr/**/*.md',
    '**/Docs/adr/**/*.md',
  ];

  const excludes = '{**/node_modules/**,**/.git/**,**/.venv/**}';
  const checks = await Promise.all(probes.map((pattern) => vscode.workspace.findFiles(pattern, excludes, 1)));
  return checks.some((matches) => matches.length > 0);
}
