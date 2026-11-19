import React, { useState, useEffect, useCallback, useRef, type ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { jwtDecode } from "jwt-decode";
import axios from "axios";
import apiClient from "../services/api";
import classService, { BrowserLogoutProofUnavailable } from "../services/classService";
import { AuthContext, type LogoutConfirmation } from "./AuthContext";
import { advanceAuthSessionGeneration, getAuthSessionGeneration } from "../utils/authSessionGeneration";
import type { User, TokenPayload, UserRole, Booking, Client } from "../types";

interface AuthProviderProps { children: ReactNode; }
const LEGACY_ACCESS = "access_token";
const PENDING_LOGOUT = "fitflow_logout_pending";
const PENDING_CSRF = "fitflow_logout_csrf";
const SYNC_KEY = "fitflow_browser_auth_epoch";

/** Broadcast only a non-secret state-change signal; never a bearer or CSRF. */
const notifyOtherTabs = (action: string): void => {
  localStorage.setItem(SYNC_KEY, `${action}|${Date.now()}|${crypto.randomUUID()}`);
};

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  // Modern access bearer stays in memory; legacy SID-less access is read
  // from localStorage only until its original signed expiry.
  const [token, setToken] = useState<string | null>(null);
  const [csrfToken, setCsrfToken] = useState<string | null>(null);
  const csrfRef = useRef<string | null>(null);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [userRole, setUserRole] = useState<UserRole | null>(null);
  const [isLoadingAuth, setIsLoadingAuth] = useState(true);
  const [logoutConfirmation, setLogoutConfirmation] = useState<LogoutConfirmation>('idle');
  const [currentClient] = useState<Client | null>(null);
  const queryClient = useQueryClient();

  const decodeToken = useCallback((accessToken: string | null) => {
    if (!accessToken) {
      setCurrentUser(null);
      setUserRole(null);
      delete apiClient.defaults.headers.common["Authorization"];
      return;
    }
    try {
      const decoded = jwtDecode<TokenPayload>(accessToken);
      if (typeof decoded.exp !== 'number' || decoded.exp * 1000 <= Date.now()) {
        throw new Error('Access token expired');
      }
      setCurrentUser({ email: decoded.sub!, role: decoded.role! });
      setUserRole(decoded.role || null);
      apiClient.defaults.headers.common["Authorization"] = `Bearer ${accessToken}`;
    } catch {
      localStorage.removeItem(LEGACY_ACCESS);
      setToken(null);
      setCurrentUser(null);
      setUserRole(null);
      delete apiClient.defaults.headers.common["Authorization"];
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    const generation = getAuthSessionGeneration();
    if (sessionStorage.getItem(PENDING_LOGOUT) === '1') {
      csrfRef.current = sessionStorage.getItem(PENDING_CSRF);
      setCsrfToken(csrfRef.current);
      setLogoutConfirmation('pending');
      setIsLoadingAuth(false);
      return;
    }
    const previous = localStorage.getItem(LEGACY_ACCESS);
    if (previous) {
      try {
        const decoded = jwtDecode<TokenPayload>(previous);
        if (!decoded.sid && typeof decoded.exp === 'number' &&
            decoded.exp * 1000 > Date.now()) {
          setToken(previous);
          decodeToken(previous);
          setIsLoadingAuth(false);
          return;
        }
      } catch { /* invalid signed token is not revived */ }
      localStorage.removeItem(LEGACY_ACCESS);
    }
    void classService.restoreBrowserSession().then((session) => {
      if (cancelled || generation !== getAuthSessionGeneration()) return;
      csrfRef.current = session.csrf_token;
      setCsrfToken(session.csrf_token);
      setToken(session.access_token);
      decodeToken(session.access_token);
      setLogoutConfirmation('idle');
    }).catch(() => {
      if (cancelled || generation !== getAuthSessionGeneration()) return;
      setToken(null);
      decodeToken(null);
    }).finally(() => {
      if (!cancelled && generation === getAuthSessionGeneration()) {
        setIsLoadingAuth(false);
      }
    });
    return () => { cancelled = true; };
  }, [decodeToken]);

  // Tabs share the HttpOnly cookie, but not React memory or sessionStorage.
  // Reconcile the actual cookie on a versioned nonsecret storage event.
  useEffect(() => {
    const onSharedSession = (event: StorageEvent) => {
      if (event.key !== SYNC_KEY || !event.newValue) return;
      const action = event.newValue.split("|")[0];
      const generation = advanceAuthSessionGeneration();
      // Initial cookie restoration may have been invalidated by this event.
      // Never leave the UI indefinitely behind the auth-loading gate.
      setIsLoadingAuth(false);
      if (action === "login") localStorage.removeItem(LEGACY_ACCESS);
      setToken(null);
      setCurrentUser(null);
      setUserRole(null);
      delete apiClient.defaults.headers.common["Authorization"];
      queryClient.clear();
      if (action === "logout-pending") {
        sessionStorage.setItem(PENDING_LOGOUT, "1");
        // CSRF belongs to the original tab's cookie snapshot. Never copy
        // that stale proof into another tab after an auth generation change.
        sessionStorage.removeItem(PENDING_CSRF);
        csrfRef.current = null;
        setCsrfToken(null);
        setLogoutConfirmation("pending");
        return;
      }
      if (action === "logout-confirmed" || action === "legacy-logout" ||
          action === "logout-expired-unconfirmed") {
        sessionStorage.removeItem(PENDING_LOGOUT);
        sessionStorage.removeItem(PENDING_CSRF);
        csrfRef.current = null;
        setCsrfToken(null);
        setLogoutConfirmation(action === "logout-confirmed" ? "confirmed" :
          action === "logout-expired-unconfirmed" ? "expired-unconfirmed" : "legacy-unconfirmed");
        return;
      }
      if (sessionStorage.getItem(PENDING_LOGOUT) === "1") {
        setLogoutConfirmation("pending");
        return; // Never abandon a pending family to follow a new cookie.
      }
      void classService.restoreBrowserSession().then(session => {
        if (getAuthSessionGeneration() !== generation) return;
        csrfRef.current = session.csrf_token;
        setCsrfToken(session.csrf_token);
        setToken(session.access_token);
        decodeToken(session.access_token);
        setLogoutConfirmation("idle");
      }).catch(() => {
        if (getAuthSessionGeneration() !== generation) return;
        csrfRef.current = null;
        setCsrfToken(null);
        decodeToken(null);
      });
    };
    window.addEventListener("storage", onSharedSession);
    return () => window.removeEventListener("storage", onSharedSession);
  }, [decodeToken, queryClient]);

  const login = (accessToken: string, csrf?: string) => {
    if (sessionStorage.getItem(PENDING_LOGOUT) === "1") {
      setLogoutConfirmation("pending");
      return; // A stale login response must not erase logout recovery.
    }
    if (csrf) {
      localStorage.removeItem(LEGACY_ACCESS);
      csrfRef.current = csrf;
      setCsrfToken(csrf);
      sessionStorage.removeItem(PENDING_LOGOUT);
      sessionStorage.removeItem(PENDING_CSRF);
    } else {
      try {
        const decoded = jwtDecode<TokenPayload>(accessToken);
        if (!decoded.sid && typeof decoded.exp === 'number' &&
            decoded.exp * 1000 > Date.now()) {
          localStorage.setItem(LEGACY_ACCESS, accessToken);
        } else {
          localStorage.removeItem(LEGACY_ACCESS);
        }
      } catch { localStorage.removeItem(LEGACY_ACCESS); }
      csrfRef.current = null;
      setCsrfToken(null);
    }
    setLogoutConfirmation('idle');
    setToken(accessToken);
    decodeToken(accessToken);
    setIsLoadingAuth(false);
    queryClient.invalidateQueries({ queryKey: ["myBookings"] });
    queryClient.invalidateQueries({ queryKey: ["currentUserProfile"] });
    notifyOtherTabs("login");
  };

  const retryLogout = async (): Promise<void> => {
    const expectedGeneration = getAuthSessionGeneration();
    try {
      // Read the current cookie proof and revoke under one cross-tab Web Lock.
      // Never reuse CSRF cached before a concurrent tab changed the cookie.
      await classService.retryBrowserLogoutFromCookie();
      if (getAuthSessionGeneration() !== expectedGeneration) return;
      csrfRef.current = null;
      setCsrfToken(null);
      sessionStorage.removeItem(PENDING_LOGOUT);
      sessionStorage.removeItem(PENDING_CSRF);
      setLogoutConfirmation('confirmed');
      notifyOtherTabs("logout-confirmed");
    } catch (error) {
      if (getAuthSessionGeneration() !== expectedGeneration) return;
      if (error instanceof BrowserLogoutProofUnavailable) {
        // Missing/expired cookie means no exact revocation ACK is possible.
        // This does NOT mean PostgreSQL committed logout. Unblock a fresh
        // login only after the old cookie can no longer authenticate.
        csrfRef.current = null;
        setCsrfToken(null);
        sessionStorage.removeItem(PENDING_LOGOUT);
        sessionStorage.removeItem(PENDING_CSRF);
        setLogoutConfirmation('expired-unconfirmed');
        notifyOtherTabs("logout-expired-unconfirmed");
        return;
      }
      setLogoutConfirmation('pending');
    }
  };

  const logout = () => {
    const csrf = csrfRef.current;
    localStorage.removeItem(LEGACY_ACCESS);
    setToken(null);
    setCurrentUser(null);
    setUserRole(null);
    delete apiClient.defaults.headers.common["Authorization"];
    queryClient.clear();
    if (csrf) {
      sessionStorage.setItem(PENDING_LOGOUT, '1');
      sessionStorage.setItem(PENDING_CSRF, csrf);
      setLogoutConfirmation('pending');
      notifyOtherTabs("logout-pending");
      void retryLogout();
    } else {
      setLogoutConfirmation('legacy-unconfirmed');
      notifyOtherTabs("legacy-logout");
    }
  };

  // Bounded retries for transient refresh failures, generation-guarded.
  // HTTP 401 means durable revocation, never silently retry an invalid token.
  useEffect(() => {
    if (!token || !csrfToken) return;
    let expiry: number;
    try { expiry = jwtDecode<TokenPayload>(token).exp * 1000; }
    catch { return; }
    if (!Number.isFinite(expiry)) return;
    const generation = getAuthSessionGeneration();
    let cancelled = false;
    let inFlight = false;
    let retries = 0;
    let timer: number | undefined;
    const schedule = (ms: number) => {
      if (timer !== undefined) window.clearTimeout(timer);
      timer = window.setTimeout(() => { void refresh(); }, ms);
    };
    const refresh = async () => {
      if (cancelled || inFlight || generation !== getAuthSessionGeneration()) return;
      inFlight = true;
      try {
        const session = await classService.refreshBrowserSession(csrfToken);
        if (cancelled || generation !== getAuthSessionGeneration()) return;
        csrfRef.current = session.csrf_token;
        setCsrfToken(session.csrf_token);
        setToken(session.access_token);
        decodeToken(session.access_token);
      } catch (error) {
        if (cancelled || generation !== getAuthSessionGeneration()) return;
        if (axios.isAxiosError(error) && error.response?.status === 401) {
          csrfRef.current = null;
          setCsrfToken(null);
          setToken(null);
          decodeToken(null);
          return;
        }
        if (retries < 3) {
          const retryDelays = [2000, 5000, 10000];
          schedule(retryDelays[retries]);
          retries += 1;
        }
        // After bounded failures, online/reload recovery may retry from cookie.
        // Never manufacture a server logout ACK or persist the access bearer.
      } finally {
        inFlight = false;
      }
    };
    const onOnline = () => { if (!cancelled) void refresh(); };
    window.addEventListener("online", onOnline);
    schedule(Math.max(0, expiry - Date.now() - 60000));
    return () => {
      cancelled = true;
      if (timer !== undefined) window.clearTimeout(timer);
      window.removeEventListener("online", onOnline);
    };
  }, [token, csrfToken, decodeToken]);

  const isAuthenticated = !!token && !!currentUser;
  const isClient = userRole === "client";
  const isTrainer = userRole === "trainer";
  const isAdmin = userRole === "admin";
  const { data: userBookings, isLoading: isLoadingBookings } = useQuery<Booking[]>({
    queryKey: ["myBookings"],
    queryFn: () => classService.getMyBookings(),
    enabled: isAuthenticated && isClient,
  });
  const value = {
    token, currentClient, currentUser, userRole,
    isAuthenticated, isClient, isTrainer, isAdmin,
    login, logout, logoutConfirmation, retryLogout,
    userBookings, isLoadingBookings, isLoadingAuth,
  };
  if (isLoadingAuth) return null;
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
