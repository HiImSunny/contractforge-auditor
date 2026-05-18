// frontend/src/api/client.ts
// Typed fetch wrapper that reads VITE_API_BASE_URL (Req 8)

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly error_code: string,
    message: string,
    public readonly data?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiFetch<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });

  if (!response.ok) {
    let errorData: any = {};
    try {
      errorData = await response.json();
    } catch {}
    throw new ApiError(
      response.status,
      errorData.error_code ?? "HTTP_ERROR",
      errorData.message ?? `HTTP ${response.status}`,
      errorData
    );
  }

  return response.json() as Promise<T>;
}

export async function apiFetchBlob(path: string): Promise<Blob> {
  const url = `${BASE_URL}${path}`;
  const response = await fetch(url);
  if (!response.ok) {
    let errorData: any = {};
    try {
      errorData = await response.json();
    } catch {}
    throw new ApiError(
      response.status,
      errorData.error_code ?? "HTTP_ERROR",
      errorData.message ?? `HTTP ${response.status}`,
      errorData
    );
  }
  return response.blob();
}
