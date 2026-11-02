import React, { useState, useEffect, type ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { jwtDecode } from "jwt-decode";
import apiClient, { ensureFreshAccess } from "../services/api";
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

  const clearLocalSession = () => {
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
    let cancelled = false;
    const rehydrate = async () => {
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
        });
        if (cancelled) return;
        if (!response.data.active || response.data.id !== claim.sub ||
            response.data.role !== claim.role) {
          throw new Error("Principal mismatch");
        }
        sessionStorage.setItem(ACCESS_KEY, usableAccess);
        apiClient.defaults.headers.common["Authorization"] = `Bearer ${usableAccess}`;
        setToken(usableAccess);
        setCurrentUser(response.data);
        setUserRole(response.data.role);
      } catch (error) {
        // Network outage is not a reason to destroy a live refresh session.
        // It stays unverified (not authenticated) until the next reload/retry.
        if (!cancelled && !(axios.isAxiosError(error) && !error.response)) {
          clearLocalSession();
        }
      } finally {
        if (!cancelled) setIsLoadingAuth(false);
      }
    };
    void rehydrate();
    window.addEventListener('online', rehydrate);
    return () => {
      cancelled = true;
      window.removeEventListener('online', rehydrate);
    };
    // Initialization is deliberately performed only on mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const login = async (pair: TokenResponse): Promise<void> => {
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
      }
      throw error;
    } finally {
      setIsLoadingAuth(false);
    }
  };

  // Always clear browser state. False means server-side revocation was not
  // confirmed; callers must not claim a complete logout in that case.
  const logout = async (): Promise<boolean> => {
    const access = sessionStorage.getItem(ACCESS_KEY);
    const refresh = sessionStorage.getItem(REFRESH_KEY);
    let revoked = false;
    try {
      if (refresh) {
        const usableAccess = await ensureFreshAccess();
        await apiClient.post("/auth/logout", { refresh_token: refresh }, {
          headers: { Authorization: `Bearer ${usableAccess}` },
        });
        revoked = true;
      }
    } catch {
      revoked = false;
    } finally {
      clearLocalSession();
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
      const delay = Math.max(1000, claim.exp * 1000 - Date.now() - 20000);
      timeout = setTimeout(() => {
        void ensureFreshAccess(true).catch((error: unknown) => {
          if (axios.isAxiosError(error) &&
              (error.response?.status === 401 || error.response?.status === 403)) {
            clearLocalSession();
          } else {
            // Do not display an expired access token as an authenticated session.
            setToken(null);
            setCurrentUser(null);
            setUserRole(null);
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
