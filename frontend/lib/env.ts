/** Public API base URL for browser and Next route handlers. Dev default lives here only. */
export function getPublicApiBaseUrl(): string {
  const env = process.env.NEXT_PUBLIC_API_URL;
  if (env != null && env.length > 0) {
    return env.replace(/\/$/, "");
  }
  return "http://localhost:8000";
}
