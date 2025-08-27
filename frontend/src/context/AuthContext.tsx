import { createContext, useContext } from 'react';

// 1. Definir el tipo para el rol del usuario

// 2. Definir la forma de los datos y funciones del contexto
interface AuthContextType {
  token: string | null;
  rol: UserRole | null;
  login: (token: string, rol: UserRole) => void;
  logout: () => void;
  isLoading: boolean;
  
}

// 3. Crear el contexto con un valor inicial de undefined
//    TypeScript nos obligará a proveer un valor real más adelante.
export const AuthContext = createContext<AuthContextType | undefined>(undefined);
export type UserRole = 'admin' | 'cliente';
// Esta es la función Type Guard
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function isUserRole(value: any): value is UserRole {
  return value === 'admin' || value === 'cliente';
}
// 4. Crear un hook personalizado para consumir el contexto fácilmente
//    Esto nos evita tener que importar useContext y AuthContext en cada componente.
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    // Este error se mostrará si intentamos usar el contexto fuera de su Provider.
    // Es una buena práctica para detectar bugs temprano.
    throw new Error('useAuth debe ser utilizado dentro de un AuthProvider');
  }
  return context;
};