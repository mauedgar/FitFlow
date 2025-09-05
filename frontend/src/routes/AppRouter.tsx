import { Routes, Route } from 'react-router-dom';
import { Layout } from '../components/layout/Layout';
import { Spinner, Center } from '@chakra-ui/react';
import React, { Suspense } from 'react';
{/* Componentes lazy loading */}
const HomePage = React.lazy(() => import('../pages/HomePage'));
const AboutPage = React.lazy(() => import('../pages/AboutPage'));
const NotFoundPage = React.lazy(() => import('../pages/NotFoundPage'));
const LandingPage = React.lazy(() => import('../pages/LandingPage'));
const LoginPage = React.lazy(() => import('../pages/LoginPage'));
const RegisterPage = React.lazy(() => import('../pages/RegisterPage'));
const PlansPage = React.lazy(() => import('../pages/PlansPage'));
const ClassesPage = React.lazy(() => import('../pages/ClassesPage'));
const JoinUsPage = React.lazy(() => import('../pages/JoinUsPage'));
const NutritionPage = React.lazy(() => import('../pages/NutritionPage'));
const AdminLayout = React.lazy(() => import('../components/admin/layout/AdminLayout'));
const ProtectedRoute = React.lazy(() => import('../components/auth/ProtectedRoute'));
const AdminDashboardPage = React.lazy(() => import('../pages/admin/AdminDashboardPage'));
const ClientsPage = React.lazy(() => import('../pages/admin/ClientsPage'));
const TeachersPage = React.lazy(() => import('../pages/admin/TeachersPage'));
const CrudClassesPage = React.lazy(() => import('../pages/admin/CrudClassesPage'));
const RootAuthGuard = React.lazy(() => import('../components/auth/RootAuthGuard'));
const ClassDetailPage = React.lazy(() => import('../pages/ClassDetailPage'));



const PageLoader: React.FC = () => (
  <Center h="100vh">
    <Spinner size="xl" />
  </Center>
);

export const AppRouter: React.FC = () => {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        {/* Rutas públicas y de usuario general, envueltas en el Layout */}
        <Route path="/" element={<Layout />}>
          <Route index element={<RootAuthGuard />} />
          <Route path="landing" element={<LandingPage />} />
          <Route path="login" element={<LoginPage />} />
          <Route path="register" element={<RegisterPage />} />
          <Route path="about" element={<AboutPage />} />          
          <Route path="plans" element={<PlansPage />} />
          <Route path="classes" element={<ClassesPage />} />
          <Route path="classes/:classId" element={<ClassDetailPage />} />
          <Route path="join-us" element={<JoinUsPage />} />
          <Route path="nutrition" element={<NutritionPage />} />
          <Route element={<ProtectedRoute allowedRoles={['client', 'admin','trainer']} />}>
            <Route path="home" element={<HomePage />} />
            {/* Si tuvieras más rutas para clientes, irían aquí */}
            {/* <Route path="my-profile" element={<ProfilePage />} /> */}
          </Route>
          {/* Esta ruta se renderiza si ninguna de las anteriores coincide */}
          <Route path="*" element={<NotFoundPage/>}/>
          {/* Agrega aquí todas tus rutas futuras */}
        </Route>
        <Route element={<ProtectedRoute allowedRoles={['admin']} />}>
          {/* Todas las rutas anidadas aquí usarán el AdminLayout */}
          <Route path="/admin" element={<AdminLayout />}>
            <Route index element={<AdminDashboardPage />} />
            <Route path="clients" element={<ClientsPage />} />
            <Route path="teachers" element={<TeachersPage />} />
            <Route path="CruClasses" element={<CrudClassesPage />} />
            {/* Si un admin va a /admin/ruta-inexistente, puedes mostrar un NotFound específico */}
            <Route path="*" element={<NotFoundPage />} /> 
          </Route>
        </Route>
        <Route path="*" element={<NotFoundPage/>}/>
      </Routes>
    </Suspense>

  );
};