import { createContext } from "react";
import type { User, UserRole, Booking, Client } from "../types";

export type LogoutConfirmation = 'idle' | 'pending' | 'confirmed' | 'legacy-unconfirmed';

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
  login: (accessToken: string, csrfToken?: string) => void;
  logout: () => void;
  logoutConfirmation: LogoutConfirmation;
  retryLogout: () => Promise<void>;
  userBookings: Booking[] | undefined;
  isLoadingBookings: boolean;
  isLoadingAuth: boolean;
}

// Solo define y exporta el contexto (sin provider ni lógica de estado aquí)
export const AuthContext = createContext<AuthContextType | undefined>(undefined);