import apiClient from "../services/api";
import type { User } from "../types";
import { inspectLocalAccessClaims } from "./accessTokenClaims";
import { projectServerAuthUser } from "./authMeProfile";

/** One validated identity fetcher per generation-scoped TanStack cache key.
 * Both AuthProvider and ADMIN guards use this same query factory. UI-only
 * JWT prechecks are not cryptographic verification; FastAPI remains authority. */
export const verifiedAuthIdentityQuery = (token: string | null, sessionGeneration: number) => ({
  queryKey: ["currentUserProfile", token, sessionGeneration] as const,
  queryFn: async ({ signal }: { signal: AbortSignal }): Promise<User> => {
    if (!token) throw new Error("Missing access token");
    const claims = inspectLocalAccessClaims(token);
    const { data } = await apiClient.get<unknown>("/auth/me", {
      signal,
      headers: { Authorization: `Bearer ${token}` },
    });
    return projectServerAuthUser(claims, data);
  },
  staleTime: 30_000,
  retry: false as const,
});
