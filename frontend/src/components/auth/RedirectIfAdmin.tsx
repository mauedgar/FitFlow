// src/components/auth/RedirectIfAdmin.tsx (Refactorizado)

import React from 'react'; // Es buena práctica importar React explícitamente
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../context/useAuth'; // ⭐ Importamos de tu AuthContext completo
import { UserRole } from '../../types'; // ⭐ Importamos UserRole de tus types/index.ts

interface RedirectIfAdminProps {
  children: React.ReactNode; // ⭐ Usamos React.ReactNode para mayor flexibilidad
}

const RedirectIfAdmin: React.FC<RedirectIfAdminProps> = ({ children }) => {
  // ⭐ Usamos las nuevas propiedades de tu AuthContext
  const { isAuthenticated, userRole, isLoadingAuth } = useAuth();

  // 1. Mientras se verifica el estado de autenticación inicial, mostramos un spinner o null.
  //    Esto es importante para evitar un parpadeo o una redirección incorrecta.
  if (isLoadingAuth) {
    // Si este componente se usa en un contexto donde el spinner ya está en un nivel superior (ej. RootAuthGuard),
    // podrías devolver 'null' para no duplicar spinners. Si es un punto de entrada independiente,
    // un spinner completo es mejor. Aquí usaré null ya que HomePage suele estar después de RootAuthGuard.
    return null; 
  }

  // 2. Si el usuario está autenticado Y es un administrador, lo redirigimos a su dashboard.
  //    Es importante verificar `isAuthenticated` para asegurarnos de que `userRole` es fiable.
  if (isAuthenticated && userRole === UserRole.ADMIN) {
    return <Navigate to="/admin" replace />;
  }

  // 3. Si el usuario no es un administrador (o no está autenticado en absoluto),
  //    renderizamos el contenido hijo.
  //    Nota: Si no está autenticado, el `ProtectedRoute` (o `RootAuthGuard`) que envuelve esta ruta
  //    ya debería haberlo redirigido al `/login`. Este componente se enfoca
  //    específicamente en redirigir a los *admins* fuera de rutas "no-admin".
  return <>{children}</>; // Usamos un fragmento para envolver children si es necesario.
};

export default RedirectIfAdmin;