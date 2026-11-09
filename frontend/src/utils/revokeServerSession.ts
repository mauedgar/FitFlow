import apiClient from "../services/api";

/** Only a successful server response confirms revocation. The caller clears
 * local state first and reports failure as remote revocation UNCONFIRMED. */
export async function revokeServerSession(
  accessToken: string | null,
  refreshToken: string | null,
): Promise<void> {
  if (!accessToken || !refreshToken) {
    throw new Error("Remote logout unavailable for an incomplete/legacy session");
  }
  await apiClient.post(
    "/auth/logout",
    { refresh_token: refreshToken },
    { headers: { Authorization: `Bearer ${accessToken}` } },
  );
}
