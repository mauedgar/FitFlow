// src/components/auth/ProtectedRoute.tsx

import { Navigate, Outlet } from 'react-router-dom';
import { useAuth, type UserRole } from '../../context/AuthContext'; // Asegúrate de importar UserRole
import { Spinner, Center } from '@chakra-ui/react';

// 1. Definimos las props que el componente espera recibir
interface ProtectedRouteProps {
  allowedRoles: UserRole[]; // Un array de roles permitidos
}

// 2. Usamos las props en la definición del componente
const ProtectedRoute = ({ allowedRoles }: ProtectedRouteProps) => {
  const { rol, isLoading } = useAuth();

  if (isLoading) {
    return (
      <Center height="100vh">
        <Spinner size="xl" />
      </Center>
    );
  }

  // 3. Comparamos el rol del usuario con los roles permitidos
  //    Si el rol no existe O no está incluido en la lista, redirigimos
  if (!rol || !allowedRoles.includes(rol)) {
    return <Navigate to="/login" replace />;
  }

  // 4. Si la autorización es exitosa, renderizamos el <Outlet />
  //    React Router se encargará de poner la página correcta aquí.
  return <Outlet />;
};

export default ProtectedRoute;