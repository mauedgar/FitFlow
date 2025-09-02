import { useState, useEffect, type ReactNode } from 'react';
import { AuthContext } from './AuthContext';

type UserRole = 'admin' | 'client'|'trainer' ;

// Atendiendo a tu nota sobre TypeScript: esta es la forma más clara de tipar los children.
export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [rol, setRol] = useState<UserRole | null>(null);
  const [isLoading, setIsLoading] = useState(true); // Estado para saber si estamos rehidratando

  // 1. Efecto para rehidratar el estado desde localStorage al cargar la app
  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    const storedRol = localStorage.getItem('rol') as UserRole | null;

    if (storedToken && storedRol) {
      setToken(storedToken);
      setRol(storedRol);
    }
    setIsLoading(false); // Terminamos de cargar la data inicial
  }, []); // El array vacío asegura que se ejecute solo una vez al montar el componente

  // 2. Función para iniciar sesión
  const login = (newToken: string, newRol: UserRole) => {
    setToken(newToken);
    setRol(newRol);
    localStorage.setItem('token', newToken);
    localStorage.setItem('rol', newRol);
  };

  // 3. Función para cerrar sesión
  const logout = () => {
    setToken(null);
    setRol(null);
    localStorage.removeItem('token');
    localStorage.removeItem('rol');
  };

  // 4. El valor que será accesible por todos los componentes hijos
  const value = {
    token,
    rol,
    login,
    logout,
    isLoading,
  };
  
  // No renderizar la app hasta que sepamos si el usuario está logueado o no
  if (isLoading) {
    return null; // O un spinner de carga a pantalla completa
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}