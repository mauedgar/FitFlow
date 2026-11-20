import React, { useState, useEffect, useCallback, useRef, type ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { jwtDecode } from "jwt-decode";
import axios from "axios";
import apiClient from "../services/api";
import classService, { BrowserLogoutProofUnavailable } from "../services/classService";
import { AuthContext, type LogoutConfirmation } from "./AuthContext";
import { AUTH_SYNC_KEY, advanceAuthSessionGeneration, getAuthSessionGeneration } from "../utils/authSessionGeneration";
import type { User, TokenPayload, UserRole, Booking, Client } from "../types";

interface AuthProviderProps { children: ReactNode; }
const LEGACY_ACCESS = "access_token";
const PENDING_LOGOUT = "fitflow_logout_pending";
const PENDING_CSRF = "fitflow_logout_csrf";
const SYNC_KEY = AUTH_SYNC_KEY;

/** Broadcast only a non-secret state-change signal; never a bearer or CSRF. */
const notifyOtherTabs = (action: string): void => {
  localStorage.setItem(SYNC_KEY, `${action}|${Date.now()}|${crypto.randomUUID()}`);
};

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  // Access bearer remains in memory. No prior localStorage bearer is trusted.
  const [token, setToken] = useState<string | null>(null);
  const [csrfToken, setCsrfToken] = useState<string | null>(null);
  const csrfRef = useRef<string | null>(null);
  const retryLogoutInFlight = useRef<Promise<void> | null>(null);
  // Only a surviving tab or a reloaded pending session needs automatic
  // orphan recovery; the initiating tab already owns its original POST.
  const needsOrphanRecovery = useRef(false);
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
    const sharedEpoch = localStorage.getItem(SYNC_KEY);
    if (sessionStorage.getItem(PENDING_LOGOUT) === '1') {
      needsOrphanRecovery.current = true;
      csrfRef.current = sessionStorage.getItem(PENDING_CSRF);
      setCsrfToken(csrfRef.current);
      setLogoutConfirmation('pending');
      setIsLoadingAuth(false);
      return;
    }
    // Pre-consumer cutover: drop even signed-looking historical localStorage
    // credentials without decoding or accepting them as a browser session.
    localStorage.removeItem(LEGACY_ACCESS);
    void classService.restoreBrowserSession().then((session) => {
      // Storage events can be missed or delivered out of order. Verify the
      // shared epoch at the point of accepting an asynchronous bearer.
      if (cancelled || generation !== getAuthSessionGeneration() ||
          localStorage.getItem(SYNC_KEY) !== sharedEpoch ||
          sessionStorage.getItem(PENDING_LOGOUT) === '1') return;
      csrfRef.current = session.csrf_token;
      setCsrfToken(session.csrf_token);
      setToken(session.access_token);
      decodeToken(session.access_token);
      setLogoutConfirmation('idle');
    }).catch(() => {
      if (cancelled || generation !== getAuthSessionGeneration() ||
          localStorage.getItem(SYNC_KEY) !== sharedEpoch ||
          sessionStorage.getItem(PENDING_LOGOUT) === '1') return;
      setToken(null);
      decodeToken(null);
    }).finally(() => {
      if (!cancelled && generation === getAuthSessionGeneration() &&
          localStorage.getItem(SYNC_KEY) === sharedEpoch &&
          sessionStorage.getItem(PENDING_LOGOUT) !== '1') {
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
      const eventEpoch = event.newValue;
      // A delayed old storage event must not undo a newer logout.
      if (localStorage.getItem(SYNC_KEY) !== eventEpoch) return;
      const action = eventEpoch.split("|")[0];
      const generation = advanceAuthSessionGeneration();
      // Initial cookie restoration may have been invalidated by this event.
      // Never leave the UI indefinitely behind the auth-loading gate.
      setIsLoadingAuth(false);
      localStorage.removeItem(LEGACY_ACCESS);
      setToken(null);
      setCurrentUser(null);
      setUserRole(null);
      delete apiClient.defaults.headers.common["Authorization"];
      queryClient.clear();
      if (action === "logout-pending") {
        // The origin tab may close before POST. A surviving tab must recover
        // the signed cookie using its own bounded, deduplicated attempt.
        needsOrphanRecovery.current = true;
        sessionStorage.setItem(PENDING_LOGOUT, "1");
        // CSRF belongs to the original tab's cookie snapshot. Never copy
        // that stale proof into another tab after an auth generation change.
        sessionStorage.removeItem(PENDING_CSRF);
        csrfRef.current = null;
        setCsrfToken(null);
        setLogoutConfirmation("pending");
        return;
      }
      if (action === "logout-confirmed" ||
          action === "logout-expired-unconfirmed") {
        needsOrphanRecovery.current = false;
        sessionStorage.removeItem(PENDING_LOGOUT);
        sessionStorage.removeItem(PENDING_CSRF);
        csrfRef.current = null;
        setCsrfToken(null);
        setLogoutConfirmation(action === "logout-confirmed" ?
          "confirmed" : "expired-unconfirmed");
        return;
      }
      if (sessionStorage.getItem(PENDING_LOGOUT) === "1") {
        setLogoutConfirmation("pending");
        return; // Never abandon a pending family to follow a new cookie.
      }
      void classService.restoreBrowserSession().then(session => {
        if (getAuthSessionGeneration() !== generation ||
            localStorage.getItem(SYNC_KEY) !== eventEpoch ||
            sessionStorage.getItem(PENDING_LOGOUT) === '1') return;
        csrfRef.current = session.csrf_token;
        setCsrfToken(session.csrf_token);
        setToken(session.access_token);
        decodeToken(session.access_token);
        setLogoutConfirmation("idle");
      }).catch(() => {
        if (getAuthSessionGeneration() !== generation ||
            localStorage.getItem(SYNC_KEY) !== eventEpoch ||
            sessionStorage.getItem(PENDING_LOGOUT) === '1') return;
        csrfRef.current = null;
        setCsrfToken(null);
        decodeToken(null);
      });
    };
    window.addEventListener("storage", onSharedSession);
    return () => window.removeEventListener("storage", onSharedSession);
  }, [decodeToken, queryClient]);

  const login = (accessToken: string, csrf: string) => {
    if (sessionStorage.getItem(PENDING_LOGOUT) === "1" ||
        localStorage.getItem(SYNC_KEY)?.startsWith('logout-pending|')) {
      setLogoutConfirmation("pending");
      return; // A stale login response must not erase logout recovery.
    }
    if (!csrf || !accessToken) return; // No access-only/legacy login.
    // A successful new identity supersedes earlier async reads and retries.
    advanceAuthSessionGeneration();
    localStorage.removeItem(LEGACY_ACCESS);
    csrfRef.current = csrf;
    setCsrfToken(csrf);
    sessionStorage.removeItem(PENDING_LOGOUT);
    sessionStorage.removeItem(PENDING_CSRF);
    setLogoutConfirmation('idle');
    setToken(accessToken);
    decodeToken(accessToken);
    setIsLoadingAuth(false);
    queryClient.invalidateQueries({ queryKey: ["myBookings"] });
    queryClient.invalidateQueries({ queryKey: ["currentUserProfile"] });
    notifyOtherTabs("login");
  };

  const retryLogout = useCallback((): Promise<void> => {
    // A manual retry during an automatic retry must join its original result;
    // two same-tab GET/POST chains could otherwise overwrite a confirmed ACK.
    if (retryLogoutInFlight.current) return retryLogoutInFlight.current;
    const expectedGeneration = getAuthSessionGeneration();
    const task = (async (): Promise<void> => {
      try {
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
          // Missing/expired cookie is never a server COMMIT acknowledgement.
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
    })();
    retryLogoutInFlight.current = task;
    void task.finally(() => {
      if (retryLogoutInFlight.current === task) retryLogoutInFlight.current = null;
    });
    return task;
  }, []);

  // A peer's logout-pending signal or a tab reload is not an ACK. Try one
  // signed cookie-bound recovery after the pending UI is visible, and retry
  // only on a genuine online transition after a transient failure. The
  // existing in-flight ref and cookie Web Lock prevent same-tab duplicates.
  useEffect(() => {
    if (logoutConfirmation !== 'pending' ||
        sessionStorage.getItem(PENDING_LOGOUT) !== '1') return;
    const recover = () => {
      if (sessionStorage.getItem(PENDING_LOGOUT) === '1') void retryLogout();
    };
    window.addEventListener('online', recover);
    let timer: number | undefined;
    if (needsOrphanRecovery.current) {
      needsOrphanRecovery.current = false;
      timer = window.setTimeout(recover, 150);
    }
    return () => {
      window.removeEventListener('online', recover);
      if (timer !== undefined) window.clearTimeout(timer);
    };
  }, [logoutConfirmation, retryLogout]);

  const logout = () => {
    if (sessionStorage.getItem(PENDING_LOGOUT) === '1') {
      void retryLogout(); // Join the existing exact recovery attempt.
      return;
    }
    // Same-tab storage events do not fire in their source tab: fence every
    // in-flight refresh, login and restoration before clearing auth state.
    advanceAuthSessionGeneration();
    needsOrphanRecovery.current = false;
    sessionStorage.setItem(PENDING_LOGOUT, '1');
    localStorage.removeItem(LEGACY_ACCESS);
    setToken(null);
    setCurrentUser(null);
    setUserRole(null);
    delete apiClient.defaults.headers.common["Authorization"];
    queryClient.clear();
    // A missing in-memory CSRF does not prove the HttpOnly cookie is absent.
    // Always attempt an exact cookie-bound server logout before concluding.
    sessionStorage.removeItem(PENDING_CSRF);
    setLogoutConfirmation('pending');
    notifyOtherTabs("logout-pending");
    void retryLogout();
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
    const sharedEpoch = localStorage.getItem(SYNC_KEY);
    let cancelled = false;
    let inFlight = false;
    let retries = 0;
    let timer: number | undefined;
    const schedule = (ms: number) => {
      if (timer !== undefined) window.clearTimeout(timer);
      timer = window.setTimeout(() => { void refresh(); }, ms);
    };
    const refresh = async () => {
      if (cancelled || inFlight || generation !== getAuthSessionGeneration() ||
          localStorage.getItem(SYNC_KEY) !== sharedEpoch ||
          sessionStorage.getItem(PENDING_LOGOUT) === '1') return;
      inFlight = true;
      try {
        const session = await classService.refreshBrowserSession();
        if (cancelled || generation !== getAuthSessionGeneration() ||
            localStorage.getItem(SYNC_KEY) !== sharedEpoch ||
            sessionStorage.getItem(PENDING_LOGOUT) === '1') return;
        csrfRef.current = session.csrf_token;
        setCsrfToken(session.csrf_token);
        setToken(session.access_token);
        decodeToken(session.access_token);
      } catch (error) {
        if (cancelled || generation !== getAuthSessionGeneration() ||
            localStorage.getItem(SYNC_KEY) !== sharedEpoch ||
            sessionStorage.getItem(PENDING_LOGOUT) === '1') return;
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
