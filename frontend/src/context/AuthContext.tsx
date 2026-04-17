import { createContext } from "react";
import type { User, UserRole, Booking, Client } from "../types";

// Debes mantener el tipo sincronizado con el value de tu provider
export interface AuthContextType {
  token: string | null;
  currentUser: User | null;
  currentClient: Client | null;
  userRole: UserRole | null;
  isAuthenticated: boolean;
  isClient: boolean;
  isTrainer: boolean;
  isAdmin: boolean;
  login: (accessToken: string) => void;
  logout: () => void;
  userBookings: Booking[] | undefined;
  isLoadingBookings: boolean;
  isLoadingAuth: boolean;
}

// Solo define y exporta el contexto (sin provider ni lógica de estado aquí)
export const AuthContext = createContext<AuthContextType | undefined>(undefined);