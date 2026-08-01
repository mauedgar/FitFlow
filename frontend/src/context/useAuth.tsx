import { useContext } from "react";
import { AuthContext } from "./AuthContext";

// Hook especializado para consumir el AuthContext de forma segura
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}