import React, { useRef, useState, useEffect, type ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { jwtDecode } from "jwt-decode";
import apiClient, { ensureFreshAccess, invalidateAuthEpoch } from "../services/api";
import axios from "axios";
import classService from "../services/classService";
import { AuthContext } from "./AuthContext";
import type { User, TokenPayload, TokenResponse, UserRole, Booking, Client } from "../types";

interface AuthProviderProps {
  children: ReactNode;
}

// Refresh and access credentials live only in this browser session.
const ACCESS_KEY = "fitflow_access_token";
const REFRESH_KEY = "fitflow_refresh_token";

function checkedAccessPayload(accessToken: string): TokenPayload {
  const claim = jwtDecode<TokenPayload>(accessToken);
  if (claim.token_use !== "access" || !claim.sub || !claim.exp ||
      claim.exp <= Date.now() / 1000 ||
      !["admin", "client", "teacher", "front_desk"].includes(claim.role)) {
    throw new Error("Invalid or expired access credential");
  }
  return claim;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [token, setToken] = useState<string | null>(null);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [userRole, setUserRole] = useState<UserRole | null>(null);
  const [isLoadingAuth, setIsLoadingAuth] = useState(true);
  const [currentClient] = useState<Client | null>(null);
  const queryClient = useQueryClient();
  const recoveryTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const recoveryScheduler = useRef<(() => void) | null>(null);
  const rehydrationController = useRef<AbortController | null>(null);
  const mounted = useRef(false);
  // Reject continuations from a previous login, rehydration or logout.
  const sessionEpoch = useRef(0);

  const clearLocalSession = () => {
    sessionEpoch.current++;
    rehydrationController.current?.abort();
    if (recoveryTimer.current !== null) {
      clearTimeout(recoveryTimer.current);
      recoveryTimer.current = null;
    }
    invalidateAuthEpoch();
    sessionStorage.removeItem(ACCESS_KEY);
    sessionStorage.removeItem(REFRESH_KEY);
    // Older releases stored only access locally; do not rehydrate it.
    localStorage.removeItem("access_token");
    delete apiClient.defaults.headers.common["Authorization"];
    setToken(null);
    setCurrentUser(null);
    setUserRole(null);
    queryClient.clear();
  };

  useEffect(() => {
    mounted.current = true;
    let cancelled = false;
    let recoveryFailures = 0;
    const scheduleRecovery = () => {
      const refresh = sessionStorage.getItem(REFRESH_KEY);
      if (cancelled || !refresh || recoveryTimer.current !== null) return;
      const epoch = sessionEpoch.current;
      const delay = Math.min(30000, 1000 * 2 ** Math.min(recoveryFailures++, 5));
      const timer = setTimeout(() => {
        // A cleared callback may race with a newer retry; it cannot clear it.
        if (recoveryTimer.current !== timer) return;
        recoveryTimer.current = null;
        if (cancelled || epoch !== sessionEpoch.current ||
            sessionStorage.getItem(REFRESH_KEY) !== refresh) return;
        void rehydrate();
      }, delay);
      recoveryTimer.current = timer;
    };
    const rehydrate = async () => {
      // An online-triggered attempt supersedes any pending backoff timer;
      // otherwise that stale timer can prevent the new failure from retrying.
      if (recoveryTimer.current !== null) {
        clearTimeout(recoveryTimer.current);
        recoveryTimer.current = null;
      }
      rehydrationController.current?.abort();
      const controller = new AbortController();
      rehydrationController.current = controller;
      const epoch = ++sessionEpoch.current;
      setToken(null);
      setCurrentUser(null);
      setUserRole(null);
      localStorage.removeItem("access_token");
      const access = sessionStorage.getItem(ACCESS_KEY);
      const refresh = sessionStorage.getItem(REFRESH_KEY);
      if (!access || !refresh) {
        if (!cancelled) {
          clearLocalSession();
          setIsLoadingAuth(false);
        }
        return;
      }
      try {
        const usableAccess = await ensureFreshAccess();
        const claim = checkedAccessPayload(usableAccess);
        const response = await apiClient.get<User>("/auth/me", {
          headers: { Authorization: `Bearer ${usableAccess}` },
          signal: controller.signal,
        });
        if (cancelled || epoch !== sessionEpoch.current ||
            sessionStorage.getItem(REFRESH_KEY) !== refresh) return;
        if (!response.data.active || response.data.id !== claim.sub ||
            response.data.role !== claim.role) {
          throw new Error("Principal mismatch");
        }
        sessionStorage.setItem(ACCESS_KEY, usableAccess);
        apiClient.defaults.headers.common["Authorization"] = `Bearer ${usableAccess}`;
        setToken(usableAccess);
        setCurrentUser(response.data);
        setUserRole(response.data.role);
        recoveryFailures = 0;
        if (recoveryTimer.current !== null) {
          clearTimeout(recoveryTimer.current);
          recoveryTimer.current = null;
        }
      } catch (error) {
        if (cancelled || epoch !== sessionEpoch.current) return;
        // Keep an unverified session on transport/5xx failures; retry with a
        // bounded backoff while retaining the same session epoch and refresh.
        const transient = axios.isAxiosError(error) &&
          (!error.response || error.response.status >= 500 || error.response.status === 429);
        if (transient) scheduleRecovery();
        else clearLocalSession();
      } finally {
        if (!cancelled && epoch === sessionEpoch.current) setIsLoadingAuth(false);
      }
    };
    recoveryScheduler.current = scheduleRecovery;
    void rehydrate();
    window.addEventListener('online', rehydrate);
    return () => {
      cancelled = true;
      mounted.current = false;
      sessionEpoch.current++;
      recoveryScheduler.current = null;
      rehydrationController.current?.abort();
      if (recoveryTimer.current !== null) {
        clearTimeout(recoveryTimer.current);
        recoveryTimer.current = null;
      }
      window.removeEventListener('online', rehydrate);
    };
    // Initialization is deliberately performed only on mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const login = async (pair: TokenResponse): Promise<void> => {
    // A new login cannot display or reuse a different authenticated principal
    // while /auth/me verifies the newly issued pair. Clear old credentials and
    // cached private data before the remote verification, even if it later fails.
    clearLocalSession();
    const epoch = ++sessionEpoch.current;
    try {
      const claim = checkedAccessPayload(pair.access_token);
      if (!pair.refresh_token) throw new Error("Missing refresh token");
      const response = await apiClient.get<User>("/auth/me", {
        headers: { Authorization: `Bearer ${pair.access_token}` },
      });
      if (!response.data.active || response.data.id !== claim.sub ||
          response.data.role !== claim.role) {
        throw new Error("Authenticated principal mismatch");
      }
      if (!mounted.current || epoch !== sessionEpoch.current) throw new Error('Login superseded');
      invalidateAuthEpoch();
      sessionStorage.setItem(ACCESS_KEY, pair.access_token);
      sessionStorage.setItem(REFRESH_KEY, pair.refresh_token);
      localStorage.removeItem("access_token");
      apiClient.defaults.headers.common["Authorization"] = `Bearer ${pair.access_token}`;
      setToken(pair.access_token);
      setCurrentUser(response.data);
      setUserRole(response.data.role);
      queryClient.invalidateQueries({ queryKey: ["myBookings"] });
      queryClient.invalidateQueries({ queryKey: ["currentUserProfile"] });
    } catch (error) {
      if (!mounted.current || epoch !== sessionEpoch.current) throw error;
      // The backend already issued a refresh token. If identity validation
      // fails, attempt to revoke it instead of stranding a server session.
      if (!(axios.isAxiosError(error) && !error.response)) {
        try {
          await apiClient.post("/auth/logout", {
            refresh_token: pair.refresh_token,
          }, { headers: { Authorization: `Bearer ${pair.access_token}` } });
        } catch {
          // Revocation may be unavailable; no success is claimed.
        }
        clearLocalSession();
      } else {
        // Keep the paired credentials for safe, server-verified rehydration.
        sessionStorage.setItem(ACCESS_KEY, pair.access_token);
        sessionStorage.setItem(REFRESH_KEY, pair.refresh_token);
        setToken(null);
        setCurrentUser(null);
        setUserRole(null);
        recoveryScheduler.current?.();
      }
      throw error;
    } finally {
      if (mounted.current && epoch === sessionEpoch.current) setIsLoadingAuth(false);
    }
  };

  // Always clear browser state. False means server-side revocation was not
  // confirmed; callers must not claim a complete logout in that case.
  const logout = async (): Promise<boolean> => {
    const epoch = ++sessionEpoch.current;
    const refresh = sessionStorage.getItem(REFRESH_KEY);
    let revoked = false;
    try {
      if (refresh) {
        const usableAccess = await ensureFreshAccess();
        if (epoch !== sessionEpoch.current ||
            sessionStorage.getItem(REFRESH_KEY) !== refresh) return false;
        await apiClient.post("/auth/logout", { refresh_token: refresh }, {
          headers: { Authorization: `Bearer ${usableAccess}` },
        });
        revoked = true;
      }
    } catch {
      revoked = false;
    } finally {
      if (epoch === sessionEpoch.current &&
          sessionStorage.getItem(REFRESH_KEY) === refresh) clearLocalSession();
    }
    return revoked;
  };


  // React state follows token replacement and server-side invalidation.
  useEffect(() => {
    const renewed = () => {
      const next = sessionStorage.getItem(ACCESS_KEY);
      if (!next || !sessionStorage.getItem(REFRESH_KEY)) return;
      try {
        const claim = checkedAccessPayload(next);
        setToken(next);
        setUserRole(claim.role);
        setCurrentUser(prev => prev ? { ...prev, role: claim.role } : prev);
      } catch {
        clearLocalSession();
      }
    };
    const invalid = () => clearLocalSession();
    window.addEventListener('fitflow:access-renewed', renewed);
    window.addEventListener('fitflow:session-invalid', invalid);
    return () => {
      window.removeEventListener('fitflow:access-renewed', renewed);
      window.removeEventListener('fitflow:session-invalid', invalid);
    };
    // Session handlers intentionally share the provider lifetime.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Refresh while SPA remains open; do not wait for a protected 401.
  useEffect(() => {
    if (!token) return;
    let timeout: ReturnType<typeof setTimeout> | undefined;
    try {
      const claim = checkedAccessPayload(token);
      const expiryEpoch = sessionEpoch.current;
      const expiryRefresh = sessionStorage.getItem(REFRESH_KEY);
      const sameSession = () => mounted.current &&
        sessionEpoch.current === expiryEpoch &&
        sessionStorage.getItem(REFRESH_KEY) === expiryRefresh;
      const delay = Math.max(1000, claim.exp * 1000 - Date.now() - 20000);
      timeout = setTimeout(() => {
        if (!sameSession()) return;
        void ensureFreshAccess(true).catch((error: unknown) => {
          if (!sameSession()) return;
          if (axios.isAxiosError(error) &&
              (error.response?.status === 401 || error.response?.status === 403)) {
            clearLocalSession();
          } else {
            // Do not display an expired access token as an authenticated session.
            setToken(null);
            setCurrentUser(null);
            setUserRole(null);
            recoveryScheduler.current?.();
          }
        });
      }, delay);
    } catch {
      clearLocalSession();
    }
    return () => { if (timeout !== undefined) clearTimeout(timeout); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const isAuthenticated = !!token && !!currentUser;
  const isClient = userRole === "client";
  const isTrainer = userRole === "teacher";
  const isAdmin = userRole === "admin";

  const { data: userBookings, isLoading: isLoadingBookings } = useQuery<Booking[]>({
    queryKey: ["myBookings"],
    queryFn: () => classService.getMyBookings(),
    enabled: isAuthenticated && isClient,
  });

  const value = {
    token, currentClient, currentUser, userRole, isAuthenticated,
    isClient, isTrainer, isAdmin, login, logout, userBookings,
    isLoadingBookings, isLoadingAuth,
  };

  if (isLoadingAuth) return null;
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
