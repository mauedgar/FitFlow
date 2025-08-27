// src/components/admin/layout/AdminLayout.tsx
import { Box, Flex } from '@chakra-ui/react';
import { Outlet } from 'react-router-dom';
import AdminSideBar from './AdminSidebar'; 
import AdminNavBar from './AdminNavBar';

const AdminLayout = () => {
  const sidebarWidth = '250px'; // Define el ancho del sidebar en una variable

  return (
    // Flex principal que organiza el layout en horizontal
    <Flex>
      {/* 1. Sidebar */}
      {/* Ocupa un ancho fijo y es visible en pantallas medianas y grandes */}
      <Box 
        as="aside"
        w={sidebarWidth} 
        minH="100vh" 
        bg="gray.800" // Un color de fondo para distinguirlo
        color="white"
        display={{ base: 'none', md: 'block' }} // Oculto en móviles
      >
        <AdminSideBar />
      </Box>

      {/* 2. Contenedor del contenido principal */}
      {/* Ocupa el resto del espacio disponible */}
      <Box flex="1">
        {/* Navbar en la parte superior del contenido principal */}
        <AdminNavBar />
        
        {/* El contenido de la página actual, renderizado por el Outlet */}
        <Box as="main" p={8}>
          <Outlet />
        </Box>
      </Box>
    </Flex>
  );
};

export default AdminLayout;