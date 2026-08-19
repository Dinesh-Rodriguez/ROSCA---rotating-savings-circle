const BASE_URL = 'http://localhost:8000/api/';

export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, body: unknown) {
    super(extractMessage(body) ?? `Request failed with status ${status}`);
    this.status = status;
    this.body = body;
  }
}

function extractMessage(body: unknown): string | undefined {
  if (body && typeof body === 'object') {
    const record = body as Record<string, unknown>;
    if (typeof record.detail === 'string') {
      return record.detail;
    }
    const firstField = Object.values(record)[0];
    if (Array.isArray(firstField) && typeof firstField[0] === 'string') {
      return firstField[0];
    }
  }
  return undefined;
}

let authToken: string | null = null;

export function setAuthToken(token: string | null) {
  authToken = token;
}

type RequestOptions = Omit<RequestInit, 'body'> & {
  body?: unknown;
};

export async function apiFetch<T = unknown>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, headers, ...rest } = options;

  const requestHeaders: Record<string, string> = {
    Accept: 'application/json',
    ...(headers as Record<string, string>),
  };

  if (body !== undefined) {
    requestHeaders['Content-Type'] = 'application/json';
  }

  if (authToken) {
    requestHeaders.Authorization = `Token ${authToken}`;
  }

  const response = await fetch(`${BASE_URL}${path.replace(/^\//, '')}`, {
    ...rest,
    headers: requestHeaders,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  const isJson = response.headers.get('content-type')?.includes('application/json');
  const payload = response.status === 204 ? undefined : isJson ? await response.json() : await response.text();

  if (!response.ok) {
    throw new ApiError(response.status, payload);
  }

  return payload as T;
}
