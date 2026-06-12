const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') || 'http://localhost:8000';

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function parseResponse<T>(response: Response): Promise<T> {
  const text = await response.text();
  const data = text ? JSON.parse(text) : {};
  if (!response.ok) {
    throw new ApiError(response.status, JSON.stringify(data));
  }
  return data as T;
}

export async function apiGet<T>(path: string, query?: Record<string, string>): Promise<T> {
  const url = new URL(`${API_BASE_URL}${path}`);
  if (query) {
    Object.entries(query).forEach(([key, value]) => {
      if (value) url.searchParams.set(key, value);
    });
  }
  const response = await fetch(url.toString());
  return parseResponse<T>(response);
}

export async function apiPost<T>(path: string, body: Record<string, unknown>): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
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
  const response = await fetch(`${API_BASE_URL}/instruments/upload`, {
    method: 'POST',
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
  const response = await fetch(`${API_BASE_URL}/capture/upload`, {
    method: 'POST',
    body: form,
  });
  return parseResponse<Record<string, unknown>>(response);
}

export function getApiBaseUrl(): string {
  return API_BASE_URL;
}