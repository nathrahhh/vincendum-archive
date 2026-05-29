export function toServiceError(error: unknown, fallback: string): Error {
  if (error instanceof Error) {
    return new Error(`${fallback}: ${error.message}`);
  }
  return new Error(fallback);
}
