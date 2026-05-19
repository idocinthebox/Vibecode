import * as http from 'http';
import * as https from 'https';
import { URL } from 'url';
import {
  CaptureFailureRequest,
  CaptureResponse,
  CaptureSuccessRequest,
  ConfirmReviewRequest,
  HarvestScanRequest,
  HarvestScanResponse,
  HealthResponse,
  InjectContextRequest,
  InjectContextResponse,
  ObserveDiagnosticRequest,
  ObserveEditRequest,
  ObserveEditResponse,
  ObserveRevertRequest,
  ObserveTerminalRequest,
  ObserveTestRequest,
  PendingReviewItem,
  PreEditCheckRequest,
  PreEditCheckResponse,
  SearchMemoryRequest,
  SearchMemoryResponse,
  TokenReportResponse,
  AutoRecallRequest,
  AutoRecallResponse,
  PreCommandCheckRequest,
  PreCommandCheckResponse,
  ShareToDatabankRequest,
  ShareToDatabankResponse,
} from '../types/api';
import { createError } from '../utils/errors';

export class VibeCodeApiClient {
  private baseUrl: string;
  private defaultTimeout: number;

  constructor(baseUrl: string, defaultTimeout: number = 10000) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.defaultTimeout = defaultTimeout;
  }

  async health(): Promise<HealthResponse> {
    return this._get<HealthResponse>('/health', 5000);
  }

  async searchMemory(request: SearchMemoryRequest): Promise<SearchMemoryResponse> {
    return this._post<SearchMemoryResponse>('/memory/search', request, 20000);
  }

  async injectContext(request: InjectContextRequest): Promise<InjectContextResponse> {
    return this._post<InjectContextResponse>('/memory/inject', request, 20000);
  }

  async captureSuccess(request: CaptureSuccessRequest): Promise<CaptureResponse> {
    return this._post<CaptureResponse>('/memory/capture-success', request, 15000);
  }

  async captureFailure(request: CaptureFailureRequest): Promise<CaptureResponse> {
    return this._post<CaptureResponse>('/memory/capture-failure', request, 15000);
  }

  async tokenReport(days: number = 30): Promise<TokenReportResponse> {
    return this._post<TokenReportResponse>('/reports/tokens', { days }, 10000);
  }

  async observeEdit(request: ObserveEditRequest): Promise<ObserveEditResponse> {
    return this._post<ObserveEditResponse>('/observe/edit', request, 10000);
  }

  async observeDiagnostic(request: ObserveDiagnosticRequest): Promise<void> {
    await this._postRaw('/observe/diagnostic', request, 10000);
  }

  async observeTest(request: ObserveTestRequest): Promise<void> {
    await this._postRaw('/observe/test', request, 10000);
  }

  async observeRevert(request: ObserveRevertRequest): Promise<void> {
    await this._postRaw('/observe/revert', request, 10000);
  }

  async observeTerminal(request: ObserveTerminalRequest): Promise<void> {
    await this._postRaw('/observe/terminal', request, 10000);
  }

  async getPendingReview(): Promise<PendingReviewItem[]> {
    return this._get<PendingReviewItem[]>('/review/pending', 10000);
  }

  async confirmReview(memoryId: string, request: ConfirmReviewRequest): Promise<{ ok: boolean }> {
    return this._post<{ ok: boolean }>(`/review/${encodeURIComponent(memoryId)}/confirm`, request, 10000);
  }

  async discardReview(memoryId: string, request: ConfirmReviewRequest): Promise<{ ok: boolean }> {
    return this._post<{ ok: boolean }>(`/review/${encodeURIComponent(memoryId)}/discard`, request, 10000);
  }

  async harvestScan(request: HarvestScanRequest): Promise<HarvestScanResponse> {
    return this._post<HarvestScanResponse>('/harvest/scan', request, 60000);
  }

  async harvestPreview(request: HarvestScanRequest): Promise<HarvestScanResponse> {
    return this._post<HarvestScanResponse>('/harvest/preview', request, 60000);
  }

  async harvestReport(reportId?: string): Promise<HarvestScanResponse> {
    const query = reportId ? `?id=${encodeURIComponent(reportId)}` : '';
    return this._get<HarvestScanResponse>(`/harvest/report${query}`, 20000);
  }

  async preEditCheck(request: PreEditCheckRequest): Promise<PreEditCheckResponse> {
    return this._post<PreEditCheckResponse>('/memory/pre-edit-check', request, 15000);
  }

  async shareToDatabank(request: ShareToDatabankRequest): Promise<ShareToDatabankResponse> {
    return this._post<ShareToDatabankResponse>(
      `/pro/share/${encodeURIComponent(request.memory_type)}/${encodeURIComponent(request.memory_id)}`,
      {},
      15000
    );
  }

  async preCommandCheck(request: PreCommandCheckRequest): Promise<PreCommandCheckResponse> {
    return this._post<PreCommandCheckResponse>('/memory/check-command', request, 10000);
  }

  async autoRecallOnError(request: AutoRecallRequest): Promise<AutoRecallResponse> {
    return this._post<AutoRecallResponse>('/memory/recall-on-error', request, 15000);
  }

  private async _get<T>(path: string, timeout: number): Promise<T> {
    const url = new URL(path, this.baseUrl);
    return this._request<T>('GET', url, undefined, timeout);
  }

  private async _post<T>(path: string, body: unknown, timeout: number): Promise<T> {
    const url = new URL(path, this.baseUrl);
    return this._request<T>('POST', url, body, timeout);
  }

  private async _postRaw(path: string, body: unknown, timeout: number): Promise<void> {
    const url = new URL(path, this.baseUrl);
    await this._request<unknown>('POST', url, body, timeout, true);
  }

  private _request<T>(
    method: string,
    url: URL,
    body: unknown | undefined,
    timeout: number,
    allowNoContent: boolean = false
  ): Promise<T> {
    return new Promise((resolve, reject) => {
      const data = body ? JSON.stringify(body) : undefined;
      const options: http.RequestOptions = {
        hostname: url.hostname,
        port: url.port,
        path: url.pathname + url.search,
        method,
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
          ...(data ? { 'Content-Length': Buffer.byteLength(data) } : {}),
        },
        timeout,
      };

      const lib = url.protocol === 'https:' ? https : http;
      const req = lib.request(options, (res) => {
        let chunks = '';
        res.on('data', (chunk) => {
          chunks += chunk;
        });
        res.on('end', () => {
          if (res.statusCode && res.statusCode >= 200 && res.statusCode < 300) {
            if (allowNoContent && (!chunks || chunks.trim().length === 0)) {
              resolve(undefined as T);
              return;
            }
            try {
              const parsed = JSON.parse(chunks) as T;
              resolve(parsed);
            } catch {
              if (allowNoContent) {
                resolve(undefined as T);
              } else {
                reject(createError('INVALID_RESPONSE'));
              }
            }
          } else if (res.statusCode === 403) {
            try {
              const parsed = JSON.parse(chunks);
              if (parsed.error === 'PROJECT_NOT_ALLOWED') {
                reject(createError('PROJECT_NOT_ALLOWED'));
              } else {
                reject(createError('SERVICE_UNAVAILABLE'));
              }
            } catch {
              reject(createError('SERVICE_UNAVAILABLE'));
            }
          } else {
            reject(createError('SERVICE_UNAVAILABLE'));
          }
        });
      });

      req.on('error', () => reject(createError('SERVICE_UNAVAILABLE')));
      req.on('timeout', () => {
        req.destroy();
        reject(createError('REQUEST_TIMEOUT'));
      });

      if (data) {
        req.write(data);
      }
      req.end();
    });
  }
}
