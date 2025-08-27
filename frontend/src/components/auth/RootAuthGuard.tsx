import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import LandingPage from '../../pages/LandingPage'; // Importamos la página a renderizar por defecto
import { Spinner, Center } from '@chakra-ui/react';

const RootAuthGuard: React.FC = () => {
  const { rol, isLoading } = useAuth();

  // 1. Mientras se verifica el estado de autenticación, mostramos un spinner.
  //    Esto evita un parpadeo donde se ve el Landing antes de redirigir.
  if (isLoading) {
    return (
      <Center height="100vh">
        <Spinner size="xl" />
      </Center>
    );
  }

  // 2. Si el usuario está autenticado, decidimos a dónde enviarlo.
  if (rol) {
    if (rol === 'admin') {
      return <Navigate to="/admin" replace />;
    }
    // Si es 'cliente' o cualquier otro rol futuro, lo enviamos a su home.
    return <Navigate to="/home" replace />;
  }
  
  // 3. Si no está autenticado (rol es null), renderizamos la LandingPage.
  return <LandingPage />;
};

export default RootAuthGuard;