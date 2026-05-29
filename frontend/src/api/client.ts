/**
 * Low-level HTTP client for the FastAPI backend.
 * Dev server proxies /api → http://127.0.0.1:8000 (see vite.config.ts).
 */

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!response.ok) {
    throw new Error(`API ${response.status}: ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}
