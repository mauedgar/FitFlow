import React, { useState, useEffect, type ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import apiClient from "../services/api";
import classService from "../services/classService";
import { AuthContext } from "./AuthContext";
import type { User, UserRole, Booking, Client } from "../types";
import { inspectLocalAccessClaims } from "../utils/accessTokenClaims";
import { projectServerAuthUser } from "../utils/authMeProfile";
import { getAuthSessionGeneration } from "../utils/authSessionGeneration";

interface AuthProviderProps {
  children: ReactNode;
}

/** Frontend identity is projected from the verified /auth/me response, not
 * from untrusted local JWT claims. FastAPI owns signature and authorization. */
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [token, setToken] = useState<string | null>(localStorage.getItem("access_token"));
  const [currentClient] = useState<Client | null>(null);
  const queryClient = useQueryClient();
  // A same-JWT re-login still starts a new independent identity generation.
  const [sessionGeneration, setSessionGeneration] = useState(getAuthSessionGeneration);

  // Decode only to fail closed early on obviously invalid/expired/refresh JWTs.
  // Do not interpret token.sub as an email or token.role as a trusted permission.
  const identity = useQuery<User>({
    queryKey: ["currentUserProfile", token, sessionGeneration],
    enabled: !!token,
    retry: false,
    staleTime: 30_000,
    queryFn: async ({ signal }) => {
      if (!token) throw new Error("Missing access token");
      const claims = inspectLocalAccessClaims(token);
      const { data } = await apiClient.get<unknown>("/auth/me", {
        signal,
        headers: { Authorization: `Bearer ${token}` },
      });
      return projectServerAuthUser(claims, data);
    },
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
      localStorage.removeItem("access_token");
      setToken(null);
      delete apiClient.defaults.headers.common["Authorization"];
    }
  }, [token]);

  // A 401, missing/disabled identity or an unavailable profile never fabricates
  // a local authenticated user. A later login may establish a fresh session.
  useEffect(() => {
    if (token && identity.isError) {
      localStorage.removeItem("access_token");
      setToken(null);
      delete apiClient.defaults.headers.common["Authorization"];
    }
  }, [identity.isError, token]);

  const currentUser = token ? identity.data ?? null : null;
  const userRole: UserRole | null = currentUser?.role ?? null;
  const isLoadingAuth = !!token && identity.isPending;

  const login = (accessToken: string) => {
    localStorage.setItem("access_token", accessToken);
    setToken(accessToken);
    setSessionGeneration(getAuthSessionGeneration());
    queryClient.invalidateQueries({ queryKey: ["myBookings"] });
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    setToken(null);
    setSessionGeneration(getAuthSessionGeneration());
    delete apiClient.defaults.headers.common["Authorization"];
    queryClient.clear();
  };

  const isAuthenticated = !!token && !!currentUser;
  const isClient = userRole === "client";
  const isTrainer = userRole === "teacher" || userRole === "trainer";
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
  };

  // Public routes, including /login, must remain usable while /auth/me is
  // pending; ProtectedRoute and RootAuthGuard honor isLoadingAuth themselves.
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
