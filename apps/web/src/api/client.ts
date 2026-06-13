import { getToken } from '../auth/token';

function resolveApiBaseUrl(): string {
  const configured = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '');
  if (configured) return configured;
  // In dev, use same-origin requests so Vite's API proxy handles routing.
  if (import.meta.env.DEV) return '';
  return 'http://localhost:8000';
}

const API_BASE_URL = resolveApiBaseUrl();

function buildApiUrl(path: string): string {
  if (!API_BASE_URL) return path;
  return `${API_BASE_URL}${path}`;
}

function authHeaders(extra?: HeadersInit): HeadersInit {
  const token = getToken();
  return {
    ...(extra ?? {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function parseResponse<T>(response: Response): Promise<T> {
  const text = await response.text();
  if (!text) {
    if (!response.ok) {
      throw new ApiError(response.status, response.statusText || 'Request failed');
    }
    return {} as T;
  }

  const contentType = response.headers.get('content-type') ?? '';
  if (!contentType.includes('application/json')) {
    const snippet = text.slice(0, 120).replace(/\s+/g, ' ');
    throw new ApiError(
      response.status,
      `Expected JSON from API but received ${contentType || 'unknown content'} (${snippet})`,
    );
  }

  let data: unknown;
  try {
    data = JSON.parse(text);
  } catch {
    throw new ApiError(response.status, 'API returned invalid JSON');
  }

  if (!response.ok) {
    throw new ApiError(response.status, JSON.stringify(data));
  }
  return data as T;
}

export async function apiGet<T>(path: string, query?: Record<string, string>): Promise<T> {
  const url = API_BASE_URL
    ? new URL(`${API_BASE_URL}${path}`)
    : new URL(path, window.location.origin);
  if (query) {
    Object.entries(query).forEach(([key, value]) => {
      if (value) url.searchParams.set(key, value);
    });
  }
  const response = await fetch(url.toString(), { headers: authHeaders() });
  return parseResponse<T>(response);
}

export async function apiPost<T>(path: string, body: Record<string, unknown>): Promise<T> {
  const response = await fetch(buildApiUrl(path), {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(body),
  });
  return parseResponse<T>(response);
}

export async function uploadInstrument(
  instrumentType: string,
  file: Blob,
  filename: string,
): Promise<Record<string, unknown>> {
  const form = new FormData();
  form.append('instrument_type', instrumentType);
  form.append('file', file, filename);
  const response = await fetch(buildApiUrl('/instruments/upload'), {
    method: 'POST',
    headers: authHeaders(),
    body: form,
  });
  return parseResponse<Record<string, unknown>>(response);
}

export async function captureUpload(
  file: File,
  options?: {
    project_id?: string;
    projectId?: string;
    instrument_type?: string;
    instrumentType?: string;
    transport?: string;
  },
): Promise<Record<string, unknown>> {
  const form = new FormData();
  form.append('file', file, file.name);
  const projectId = options?.project_id ?? options?.projectId;
  const instrumentType = options?.instrument_type ?? options?.instrumentType;
  if (projectId) form.append('project_id', projectId);
  if (instrumentType) form.append('instrument_type', instrumentType);
  if (options?.transport) form.append('transport', options.transport);
  const response = await fetch(buildApiUrl('/capture/upload'), {
    method: 'POST',
    headers: authHeaders(),
    body: form,
  });
  return parseResponse<Record<string, unknown>>(response);
}

export async function uploadTrainingData(
  task: 'thin_section' | 'spectral',
  options: {
    className: string;
    projectId?: string;
    pairFile?: File;
    pplFile?: File;
    xplFile?: File;
    spectralFile?: File;
  },
): Promise<Record<string, unknown>> {
  const path =
    task === 'spectral' ? '/training/spectral/upload' : '/training/thin_section/upload';
  const form = new FormData();
  form.append('class_name', options.className);
  if (options.projectId) form.append('project_id', options.projectId);

  if (task === 'spectral') {
    if (!options.spectralFile) {
      throw new Error('spectralFile is required');
    }
    form.append('file', options.spectralFile, options.spectralFile.name);
  } else if (options.pairFile) {
    form.append('pair_file', options.pairFile, options.pairFile.name);
  } else if (options.pplFile && options.xplFile) {
    form.append('ppl_file', options.pplFile, options.pplFile.name);
    form.append('xpl_file', options.xplFile, options.xplFile.name);
  } else {
    throw new Error('Provide pairFile or both pplFile and xplFile');
  }

  const response = await fetch(buildApiUrl(path), {
    method: 'POST',
    headers: authHeaders(),
    body: form,
  });
  return parseResponse<Record<string, unknown>>(response);
}

export function getApiBaseUrl(): string {
  return API_BASE_URL || `${window.location.origin} (vite proxy)`;
}