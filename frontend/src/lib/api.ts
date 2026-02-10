import type {
  UploadResponse,
  JobResponse,
  HealthResponse,
  ConfigLanguages,
  ConfigTranslators,
  ConfigOptions,
  ConfigSourceLanguages,
  ScanCopyRequest,
  ConvertRequest,
  TranslateRequest,
} from './types';

const BASE = '/api/v1';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `Request failed with status ${res.status}`;
    try {
      const body = await res.json();
      if (body.detail) {
        detail = body.detail;
      }
    } catch {
      // response body was not JSON – keep the generic message
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

async function postJson<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return handleResponse<T>(res);
}

// ---------------------------------------------------------------------------
// Session endpoints
// ---------------------------------------------------------------------------

export async function uploadFile(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append('file', file);

  const res = await fetch(`${BASE}/sessions/upload`, {
    method: 'POST',
    body: form,
  });
  return handleResponse<UploadResponse>(res);
}

export async function deleteSession(sessionId: string): Promise<void> {
  const res = await fetch(`${BASE}/sessions/${sessionId}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    let detail = `Delete failed with status ${res.status}`;
    try {
      const body = await res.json();
      if (body.detail) {
        detail = body.detail;
      }
    } catch {
      // not JSON
    }
    throw new Error(detail);
  }
}

// ---------------------------------------------------------------------------
// Job endpoints
// ---------------------------------------------------------------------------

export async function startScanCopy(
  sessionId: string,
  config: ScanCopyRequest,
): Promise<JobResponse> {
  return postJson<JobResponse>(
    `${BASE}/sessions/${sessionId}/scan-copy`,
    config,
  );
}

export async function startConvert(
  sessionId: string,
  config: ConvertRequest,
): Promise<JobResponse> {
  return postJson<JobResponse>(
    `${BASE}/sessions/${sessionId}/convert`,
    config,
  );
}

export async function startTranslate(
  sessionId: string,
  config: TranslateRequest,
): Promise<JobResponse> {
  return postJson<JobResponse>(
    `${BASE}/sessions/${sessionId}/translate`,
    config,
  );
}

// ---------------------------------------------------------------------------
// Download
// ---------------------------------------------------------------------------

export function getDownloadUrl(sessionId: string): string {
  return `${BASE}/sessions/${sessionId}/download`;
}

// ---------------------------------------------------------------------------
// Config / Health
// ---------------------------------------------------------------------------

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${BASE}/health`);
  return handleResponse<HealthResponse>(res);
}

export async function fetchLanguages(): Promise<ConfigLanguages> {
  const res = await fetch(`${BASE}/config/languages`);
  return handleResponse<ConfigLanguages>(res);
}

export async function fetchTranslators(): Promise<ConfigTranslators> {
  const res = await fetch(`${BASE}/config/translators`);
  return handleResponse<ConfigTranslators>(res);
}

export async function fetchOptions(): Promise<ConfigOptions> {
  const res = await fetch(`${BASE}/config/options`);
  return handleResponse<ConfigOptions>(res);
}

export async function fetchSourceLanguages(): Promise<ConfigSourceLanguages> {
  const res = await fetch(`${BASE}/config/source-languages`);
  return handleResponse<ConfigSourceLanguages>(res);
}
