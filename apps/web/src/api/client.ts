import { getToken } from '../auth/token';

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') || 'http://localhost:8000';

function authHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
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
  const response = await fetch(url.toString(), { headers: authHeaders() });
  return parseResponse<T>(response);
}

export async function apiPost<T>(path: string, body: Record<string, unknown>): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
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
    headers: authHeaders(),
    body: form,
  });
  return parseResponse<Record<string, unknown>>(response);
}

export function getApiBaseUrl(): string {
  return API_BASE_URL;
}