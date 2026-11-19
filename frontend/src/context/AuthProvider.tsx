import React, { useState, useEffect, useCallback, useRef, type ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { jwtDecode } from "jwt-decode";
import apiClient from "../services/api";
import classService from "../services/classService";
import { AuthContext, type LogoutConfirmation } from "./AuthContext";
import { getAuthSessionGeneration } from "../utils/authSessionGeneration";
import type { User, TokenPayload, UserRole, Booking, Client } from "../types";

interface AuthProviderProps { children: ReactNode; }
const LEGACY_ACCESS = "access_token";
const PENDING_LOGOUT = "fitflow_logout_pending";
const PENDING_CSRF = "fitflow_logout_csrf";

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
    }).finally(() => { if (!cancelled) setIsLoadingAuth(false); });
    return () => { cancelled = true; };
  }, [decodeToken]);

  const login = (accessToken: string, csrf?: string) => {
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
  };

  const retryLogout = async (): Promise<void> => {
    const csrf = csrfRef.current ?? sessionStorage.getItem(PENDING_CSRF);
    if (!csrf) {
      setLogoutConfirmation('pending');
      return;
    }
    const expectedGeneration = getAuthSessionGeneration();
    try {
      await classService.logoutBrowserSession(csrf);
      if (getAuthSessionGeneration() !== expectedGeneration) return;
      csrfRef.current = null;
      setCsrfToken(null);
      sessionStorage.removeItem(PENDING_LOGOUT);
      sessionStorage.removeItem(PENDING_CSRF);
      setLogoutConfirmation('confirmed');
    } catch {
      if (getAuthSessionGeneration() === expectedGeneration) {
        setLogoutConfirmation('pending');
      }
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
      void retryLogout();
    } else {
      setLogoutConfirmation('legacy-unconfirmed');
    }
  };

  useEffect(() => {
    if (!token || !csrfToken) return;
    let expiry: number;
    try { expiry = jwtDecode<TokenPayload>(token).exp * 1000; }
    catch { return; }
    if (!Number.isFinite(expiry)) return;
    let cancelled = false;
    const timer = window.setTimeout(() => {
      void classService.refreshBrowserSession(csrfToken).then((session) => {
        if (cancelled) return;
        csrfRef.current = session.csrf_token;
        setCsrfToken(session.csrf_token);
        setToken(session.access_token);
        decodeToken(session.access_token);
      }).catch(() => { /* Backend guards still enforce expiry. */ });
    }, Math.max(0, expiry - Date.now() - 60000));
    return () => { cancelled = true; window.clearTimeout(timer); };
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
