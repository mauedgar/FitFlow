import React, { useState, useEffect, useCallback, type ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { jwtDecode } from "jwt-decode";
import apiClient from "../services/api";
import classService from "../services/classService";
import { AuthContext } from "./AuthContext";
import type { User, TokenPayload, UserRole, Booking, Client } from "../types";

interface AuthProviderProps {
  children: ReactNode;
}

// Componente Provider que maneja la lógica de autenticación y provee el contexto
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [token, setToken] = useState<string | null>(localStorage.getItem("access_token"));
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [userRole, setUserRole] = useState<UserRole | null>(null);
  const [isLoadingAuth, setIsLoadingAuth] = useState(true);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [currentClient, SetCurrentClient] = useState<Client | null> (null);
  const queryClient = useQueryClient();

  // Decodifica el accessToken y setea el usuario y rol
  const decodeToken = useCallback((accessToken: string | null) => {
    if (!accessToken) {
      setCurrentUser(null);
      setUserRole(null);
      setIsLoadingAuth(false);
      delete apiClient.defaults.headers.common["Authorization"];
      return;
    }
    try {
      const decoded: TokenPayload = jwtDecode(accessToken);
      setCurrentUser({ email: decoded.sub!, role: decoded.role! });
      setUserRole(decoded.role || null);
      apiClient.defaults.headers.common["Authorization"] = `Bearer ${accessToken}`;
    } catch (error) {
      // Manejo de error si el token está corrupto o expiró
      console.error("Failed to decode token:", error);
      localStorage.removeItem("access_token");
      setToken(null);
      setCurrentUser(null);
      setUserRole(null);
      delete apiClient.defaults.headers.common["Authorization"];
    } finally {
      setIsLoadingAuth(false);
    }
  }, []);

  // Al montar, intenta rehidratar el token y usuario desde localStorage
  useEffect(() => {
    const storedToken = localStorage.getItem("access_token");
    setToken(storedToken);
    decodeToken(storedToken);
    if (!storedToken) setIsLoadingAuth(false); // Si no hay token, termina la carga inicial
  }, [decodeToken]);

  // Login: guarda el token y decodifica
  const login = (accessToken: string) => {
    localStorage.setItem("access_token", accessToken);
    setToken(accessToken);
    decodeToken(accessToken);
    queryClient.invalidateQueries({ queryKey: ["myBookings"] });
    queryClient.invalidateQueries({ queryKey: ["currentUserProfile"] });
  };

  // Logout: limpia todo el estado y la cache de queries
  const logout = () => {
    localStorage.removeItem("access_token");
    setToken(null);
    setCurrentUser(null);
    setUserRole(null);
    delete apiClient.defaults.headers.common["Authorization"];
    queryClient.clear();
  };

  const isAuthenticated = !!token && !!currentUser;
  const isClient = userRole === "client";
  const isTrainer = userRole === "trainer";
  const isAdmin = userRole === "admin";

  // TanStack Query obtiene los bookings SOLO si está autenticado y es cliente
  const { data: userBookings, isLoading: isLoadingBookings } = useQuery<Booking[]>({
    queryKey: ["myBookings"],
    queryFn: () => {
    return classService.getMyBookings();
    },    
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

  if (isLoadingAuth) {
    // Puedes poner aquí tu spinner o Skeleton si lo prefieres
    return null;
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};