import React, { useState, useEffect, type ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import apiClient from "../services/api";
import classService from "../services/classService";
import { AuthContext } from "./AuthContext";
import type { User, UserRole, Booking, Client } from "../types";
import { inspectLocalAccessClaims } from "../utils/accessTokenClaims";
import { verifiedAuthIdentityQuery } from "../utils/verifiedAuthIdentityQuery";
import { advanceAuthSessionGeneration, getAuthSessionGeneration } from "../utils/authSessionGeneration";
import { revokeServerSession } from "../utils/revokeServerSession";
import { isRecoverableIdentityFailure } from "../utils/identityFailurePolicy";

interface AuthProviderProps {
  children: ReactNode;
}

// Non-secret attempt identifiers preserve which remote logouts remain unknown.
// Never write JWTs, refresh hashes, email or user IDs to this ledger.
const PENDING_LOGOUTS_KEY = "fitflow_logout_pending_attempts";
const REMOTE_UNCONFIRMED_KEY = "fitflow_logout_remote_unconfirmed";
const UNKNOWN_LOGOUT = "unrecognized-pending";
const MAX_RECORDED_LOGOUTS = 24;
// Volatile fallback is deliberately sticky: a storage exception is not an ACK.
// No credential, subject, email or account identifier is ever stored here.
const inFlightLogoutIds = new Set<string>();
let storageUncertainty = false;

function boundLogoutIds(ids: string[]): string[] {
  const unique = [...new Set(ids.filter(id => typeof id === "string" && id.length > 0))];
  if (unique.length <= MAX_RECORDED_LOGOUTS) return unique;
  // Compaction must not turn any discarded unresolved logout into success.
  return [UNKNOWN_LOGOUT, ...unique.filter(id => id !== UNKNOWN_LOGOUT).slice(-(MAX_RECORDED_LOGOUTS - 1))];
}

function pendingLogoutAttempts(): string[] {
  const pending: string[] = [];
  try {
    const raw = sessionStorage.getItem(PENDING_LOGOUTS_KEY);
    if (raw !== null) {
      try {
        const ids: unknown = JSON.parse(raw);
        if (Array.isArray(ids) && ids.length > 0 &&
            ids.length <= MAX_RECORDED_LOGOUTS &&
            ids.every((id: unknown) => typeof id === "string" && id.length > 0)) {
          pending.push(...ids as string[]);
        } else {
          pending.push(UNKNOWN_LOGOUT);
        }
      } catch {
        pending.push(UNKNOWN_LOGOUT);
      }
    }
    const flag = sessionStorage.getItem(REMOTE_UNCONFIRMED_KEY);
    if (flag === "1" && raw === null) pending.push("legacy-unconfirmed");
    // A corrupt flag cannot cancel a non-empty ledger; preserve uncertainty.
    if (flag !== null && flag !== "1") pending.push(UNKNOWN_LOGOUT);
  } catch {
    storageUncertainty = true;
  }
  pending.push(...inFlightLogoutIds);
  if (storageUncertainty) pending.push(UNKNOWN_LOGOUT);
  return boundLogoutIds(pending);
}

function persistLogoutAttempts(ids: string[]): boolean {
  const bounded = boundLogoutIds(ids);
  try {
    if (bounded.length > 0) {
      sessionStorage.setItem(PENDING_LOGOUTS_KEY, JSON.stringify(bounded));
      sessionStorage.setItem(REMOTE_UNCONFIRMED_KEY, "1");
    } else {
      sessionStorage.removeItem(PENDING_LOGOUTS_KEY);
      sessionStorage.removeItem(REMOTE_UNCONFIRMED_KEY);
    }
  } catch {
    // The tab cannot honestly attest a durable warning or revocation.
    storageUncertainty = true;
  }
  return bounded.length > 0 || storageUncertainty;
}

/** Frontend identity is projected from the verified /auth/me response, not
 * from untrusted local JWT claims. FastAPI owns signature and authorization. */
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => {
    // Incomplete or persistent access-only sessions require a new login.
    try {
      localStorage.removeItem("access_token");
      const access = sessionStorage.getItem("access_token");
      const refresh = sessionStorage.getItem("refresh_token");
      if (!access || !refresh) {
        sessionStorage.removeItem("access_token");
        sessionStorage.removeItem("refresh_token");
        return null;
      }
      return access;
    } catch {
      // A browser storage failure must not authorize a stale identity.
      storageUncertainty = true;
      return null;
    }
  });
  const [currentClient] = useState<Client | null>(null);
  // A non-secret warning survives tab reload; never persist a JWT after logout.
  const [remoteLogoutUnconfirmed, setRemoteLogoutUnconfirmed] = useState(
    () => pendingLogoutAttempts().length > 0,
  );
  const queryClient = useQueryClient();
  // A same-JWT re-login still starts a new independent identity generation.
  const [sessionGeneration, setSessionGeneration] = useState(getAuthSessionGeneration);

  // Decode only to fail closed early on obviously invalid/expired/refresh JWTs.
  // Do not interpret token.sub as an email or token.role as a trusted permission.
  const identity = useQuery<User>({
    ...verifiedAuthIdentityQuery(token, sessionGeneration),
    enabled: !!token,
  });

  useEffect(() => {
    if (!token) {
      delete apiClient.defaults.headers.common["Authorization"];
      return;
    }
    try {
      inspectLocalAccessClaims(token);
      apiClient.defaults.headers.common["Authorization"] = `Bearer ${token}`;
    } catch {
      sessionStorage.removeItem("access_token");
      sessionStorage.removeItem("refresh_token");
      setToken(null);
      delete apiClient.defaults.headers.common["Authorization"];
    }
  }, [token]);

  // A transient outage cannot establish permissions or prove server revocation.
  // Keep both tab-scoped credentials for an explicit recovery or remote logout.
  const identityRecoveryPending = !!token && identity.isError &&
    isRecoverableIdentityFailure(identity.error);
  useEffect(() => {
    if (token && identity.isError && !isRecoverableIdentityFailure(identity.error)) {
      sessionStorage.removeItem("access_token");
      sessionStorage.removeItem("refresh_token");
      setToken(null);
      delete apiClient.defaults.headers.common["Authorization"];
    }
  }, [identity.isError, identity.error, token]);

  // Previously cached identity data must not authorize a failed refetch.
  const currentUser = token && identity.isSuccess ? identity.data ?? null : null;
  const userRole: UserRole | null = currentUser?.role ?? null;
  const isLoadingAuth = !!token &&
    (identity.isPending || (identityRecoveryPending && identity.isFetching));
  const retryIdentity = async (): Promise<void> => {
    if (token) await identity.refetch();
  };

  const login = (accessToken: string, refreshToken: string) => {
    // Both credentials remain tab-scoped: no persistent access bearer.
    if (!refreshToken) throw new Error("Falta el token para revocar la sesión");
    sessionStorage.setItem("refresh_token", refreshToken);
    sessionStorage.setItem("access_token", accessToken);
    setToken(accessToken);
    setSessionGeneration(advanceAuthSessionGeneration());
    queryClient.invalidateQueries({ queryKey: ["myBookings"] });
  };

  const logout = async (): Promise<void> => {
    // Snapshot credentials before synchronously dropping UI authentication.
    const accessToken = token;
    let refreshToken: string | null = null;
    try {
      refreshToken = sessionStorage.getItem("refresh_token");
      sessionStorage.removeItem("refresh_token");
      sessionStorage.removeItem("access_token");
    } catch {
      // Local in-memory auth must still close; remote credentials are unknown.
      storageUncertainty = true;
    }
    setToken(null);
    const logoutGeneration = advanceAuthSessionGeneration();
    setSessionGeneration(logoutGeneration);
    delete apiClient.defaults.headers.common["Authorization"];
    queryClient.clear();
    // The generation prevents stale UI identity reuse; each remote logout
    // also needs its own non-secret attempt ID to avoid false cross-session ACK.
    const attemptId = [
      "logout", String(logoutGeneration), String(Date.now()),
      Math.random().toString(36).slice(2),
    ].join("-");
    inFlightLogoutIds.add(attemptId);
    setRemoteLogoutUnconfirmed(
      persistLogoutAttempts(pendingLogoutAttempts()),
    );
    try {
      // Only a verified remote HTTP 204 resolves *this* logout attempt.
      await revokeServerSession(accessToken, refreshToken);
      inFlightLogoutIds.delete(attemptId);
      const remaining = pendingLogoutAttempts().filter((entry) => entry !== attemptId);
      setRemoteLogoutUnconfirmed(persistLogoutAttempts(remaining));
    } catch (error) {
      inFlightLogoutIds.delete(attemptId);
      // Keep the attempt in the durable ledger, or an unknown sticky marker
      // when browser storage is unavailable. Never fabricate a remote ACK.
      setRemoteLogoutUnconfirmed(true);
      throw error;
    }
  };

  const dismissRemoteLogoutWarning = () => {
    // Dismisses the visible notice for this rendering only. The durable
    // non-secret pending ledger and warning flag survive a reload until ACK.
    setRemoteLogoutUnconfirmed(false);
  };

  const isAuthenticated = !!token && !!currentUser;
  const isClient = userRole === "client";
  const isTrainer = userRole === "teacher"; // Backend role only; trainer is a UI legacy alias.
  const isAdmin = userRole === "admin";

  const { data: userBookings, isLoading: isLoadingBookings } = useQuery<Booking[]>({
    queryKey: ["myBookings"],
    queryFn: () => classService.getMyBookings(),
    enabled: isAuthenticated && isClient,
  });

  const value = {
    token,
    currentClient,
    currentUser,
    userRole,
    isAuthenticated,
    isClient,
    isTrainer,
    isAdmin,
    login,
    logout,
    userBookings,
    isLoadingBookings,
    isLoadingAuth,
    identityRecoveryPending,
    retryIdentity,
    remoteLogoutUnconfirmed,
    dismissRemoteLogoutWarning,
  };

  // Public routes, including /login, must remain usable while /auth/me is
  // pending; ProtectedRoute and RootAuthGuard honor isLoadingAuth themselves.
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
