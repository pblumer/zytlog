export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1';

export class ApiError extends Error {
  status: number;
  details?: unknown;

  constructor(status: number, message: string, details?: unknown) {
    super(message);
    this.status = status;
    this.details = details;
  }
}

type RequestOptions = Omit<RequestInit, 'headers'> & {
  headers?: Record<string, string>;
  token?: string | null;
};

async function parseResponse(response: Response) {
  const contentType = response.headers.get('content-type') ?? '';
  if (contentType.includes('application/json')) {
    return response.json();
  }
  return response.text();
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {
    Accept: 'application/json',
    ...(options.body ? { 'Content-Type': 'application/json' } : {}),
    ...(options.headers ?? {}),
  };

  if (options.token) {
    headers.Authorization = `Bearer ${options.token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    credentials: 'include',
    ...options,
    headers,
  });

  const data = await parseResponse(response);

  if (!response.ok) {
    const detail = typeof data === 'object' && data && 'detail' in data ? String((data as { detail?: unknown }).detail) : null;
    throw new ApiError(response.status, detail ?? `Request failed (${response.status})`, data);
  }

  return data as T;
}

export function apiGet<T>(path: string, token?: string | null): Promise<T> {
  return apiRequest<T>(path, { method: 'GET', token });
}

export function apiPost<T>(path: string, body?: unknown, token?: string | null): Promise<T> {
  return apiRequest<T>(path, {
    method: 'POST',
    body: body !== undefined ? JSON.stringify(body) : undefined,
    token,
  });
}
