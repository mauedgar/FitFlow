// src/components/auth/RootAuthGuard.tsx (Refactorizado)

import React from 'react';
import { Navigate } from 'react-router-dom';
import { Spinner, Center, Text } from '@chakra-ui/react'; // Añadimos Text para mejor UX
import { useAuth } from '../../context/useAuth'; // ⭐ Importamos de tu AuthContext completo
import LandingPage from '../../pages/LandingPage'; // Importamos la página a renderizar por defecto
import { UserRole } from '../../types';

const RootAuthGuard: React.FC = () => {
  // ⭐ Usamos las nuevas propiedades de tu AuthContext
  const { isAuthenticated, userRole, isLoadingAuth } = useAuth();

  // 1. Mientras se verifica el estado de autenticación inicial, mostramos un spinner.
  //    Esto evita cualquier parpadeo indeseado antes de que el AuthContext se rehidrate.
  if (isLoadingAuth) {
    return (
      <Center height="100vh" flexDirection="column" p={4}>
        <Spinner size="xl" color="teal.500" thickness="4px" speed="0.65s" emptyColor="gray.200" mb={4} />
        <Text fontSize="lg" color="gray.600">Verificando sesión...</Text>
      </Center>
    );
  }
  // 2. Si el usuario está autenticado, decidimos a dónde enviarlo basado en su rol.
  if (isAuthenticated && userRole !== null) { // Aseguramos que hay un rol para la redirección
    if (userRole === UserRole.ADMIN) {
      return <Navigate to="/admin" replace />;
    }
    // Si es 'client' o 'trainer' (o cualquier otro rol futuro que tenga un home específico)
    // El rol 'trainer' también podría ir a '/home' o a un '/trainer-dashboard'
    return <Navigate to="/home" replace />; // 'home' suele ser la página principal para usuarios logueados
  }
  
  // 3. Si no está autenticado (isAuthenticated es false), renderizamos la LandingPage.
  //    No hay necesidad de verificar 'userRole' aquí porque 'isAuthenticated' ya lo descarta.
  return <LandingPage />;
};

export default RootAuthGuard;