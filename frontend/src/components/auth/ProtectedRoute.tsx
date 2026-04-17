// src/components/auth/ProtectedRoute.tsx (Refactorizado)

import React from 'react'; // Es buena práctica importar React explícitamente
import { Navigate, Outlet } from 'react-router-dom';
import { Spinner, Center, Text } from '@chakra-ui/react'; // Añadimos Text para mensajes
import { useAuth } from '../../context/useAuth'; // ⭐ Importamos directamente AuthContext
import { UserRole } from '../../types'; // ⭐ Importamos UserRole de tus types/index.ts

// 1. Definimos las props que el componente espera recibir
interface ProtectedRouteProps {
  allowedRoles: UserRole[]; // Un array de roles permitidos
  redirectTo?: string;      // Opcional: la ruta a redirigir si no está autorizado
}

// 2. Usamos las props en la definición del componente
const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ allowedRoles, redirectTo = "/login" }) => {
  // ⭐ Usamos las nuevas propiedades del AuthContext
  const { isAuthenticated, userRole, isLoadingAuth } = useAuth();

  // 3. Manejar el estado de carga inicial de la autenticación
  if (isLoadingAuth) {
    return (
      <Center height="100vh" flexDirection="column" p={4}>
        <Spinner size="xl" color="teal.500" thickness="4px" speed="0.65s" emptyColor="gray.200" mb={4} />
        <Text fontSize="lg" color="gray.600">Cargando perfil de usuario...</Text>
      </Center>
    );
  }

  // 4. Verificar si el usuario está autenticado
  if (!isAuthenticated) {
    // Si no está autenticado, redirigimos a la página de login (o la ruta especificada)
    return <Navigate to={redirectTo} replace />;
  }

  // 5. Si está autenticado, verificar si tiene un rol permitido
  //    Comparamos el rol del usuario con los roles permitidos
  //    `userRole` del AuthContext ya es de tipo `UserRole | null`, así que el includes es seguro si no es null
  if (userRole === null || !allowedRoles.includes(userRole)) {
    // Si el rol no está permitido, redirigimos. Podrías redirigir a una página de "Acceso Denegado"
    // en lugar de login si ya está logueado pero con un rol incorrecto.
    // Por ahora, para simplificar, sigue redirigiendo a login, pero idealmente sería algo como '/unauthorized'.
    return <Navigate to={'/'} replace />; 
  }

  // 6. Si la autenticación y autorización son exitosas, renderizamos el <Outlet />
  //    React Router se encargará de poner la página correcta aquí.
  return <Outlet />;
};

export default ProtectedRoute;