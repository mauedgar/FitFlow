import { Navigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

interface RedirectIfAdminProps {
  children: React.ReactElement;
}

const RedirectIfAdmin: React.FC<RedirectIfAdminProps> = ({ children }) => {
  const { rol, isLoading } = useAuth();

  // Si aún estamos verificando la autenticación, no hacemos nada todavía.
  // El ProtectedRoute que envuelve a HomePage ya se encargará de esto.
  if (isLoading) {
    return null; // O un spinner si se prefiere
  }

  // Si el usuario está logueado y es admin, lo redirigimos a su dashboard.
  if (rol === 'admin') {
    return <Navigate to="/admin" replace />;
  }

  // Si no es admin (o no está logueado), renderizamos la página solicitada (HomePage).
  return children;
};

export default RedirectIfAdmin;