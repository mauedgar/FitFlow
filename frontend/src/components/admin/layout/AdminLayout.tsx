import { Box, Flex, useBreakpointValue } from '@chakra-ui/react';
import { Outlet } from 'react-router-dom';
import AdminSideBar from './AdminSidebar';
import AdminNavBar from './AdminNavBar';

const AdminLayout = () => {
  const sidebarWidth = '250px';
  const showSidebar = useBreakpointValue({ base: false, md: true });

  return (
    <Flex minH="100vh" bg="gray.50">
      {/* SIDEBAR - Solo en pantallas medianas y grandes */}
      {showSidebar && (
        <Box
          as="aside"
          w={sidebarWidth}
          minH="100vh"
          bg="gray.800"
          color="white"
          position="fixed"
          left="0"
          top="0"
          zIndex="1000"
        >
          <AdminSideBar />
        </Box>
      )}

      {/* CONTENIDO PRINCIPAL */}
      <Box
        flex="1"
        ml={showSidebar ? sidebarWidth : '0'}
        transition="margin-left 0.2s"
      >
        {/* NAVBAR */}
        <AdminNavBar />

        {/* ÁREA DE CONTENIDO */}
        <Box as="main" p={{ base: 4, md: 8 }} minH="calc(100vh - 64px)">
          <Outlet />
        </Box>
      </Box>
    </Flex>
  );
};

export default AdminLayout;