import apiClient from "../services/api";

// One bounded retry is safe only because Redis records the exact signed
// refresh revocation as an idempotent acknowledgement. No bearer is persisted.
function isTransientRevocationFailure(error: unknown): boolean {
  if (typeof error !== "object" || error === null) return false;
  const candidate = error as { response?: { status?: number }; request?: unknown };
  if (candidate.response) {
    return [429, 502, 503, 504].includes(candidate.response.status ?? 0);
  }
  return candidate.request != null;
}

/** Only a confirmed HTTP response completes remote logout.
 * Failed retries remain UNCONFIRMED; local deauthorization is unchanged. */
export async function revokeServerSession(
  accessToken: string | null,
  refreshToken: string | null,
): Promise<void> {
  if (!accessToken || !refreshToken) {
    throw new Error("Remote logout unavailable for an incomplete/legacy session");
  }
  const request = async (): Promise<void> => {
    const response = await apiClient.post(
      "/auth/logout",
      { refresh_token: refreshToken },
      { headers: { Authorization: "Bearer " + accessToken } },
    );
    // Axios resolves any HTTP 2xx. Revocation is confirmed ONLY by 204.
    // A 200/202 is not a remote logout receipt and must fail closed.
    if (response.status !== 204) {
      throw new Error("Remote logout UNCONFIRMED: expected HTTP 204");
    }
  };
  try {
    await request();
  } catch (error) {
    if (!isTransientRevocationFailure(error)) throw error;
    await request();
  }
}
