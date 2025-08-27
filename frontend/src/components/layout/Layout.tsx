import { Outlet } from 'react-router-dom';
import { Box, Flex, PortalManager } from '@chakra-ui/react';
import { Navbar } from './Navbar';
import { Footer } from '../Footer/Footer';

export const Layout: React.FC = () => {
  return (
    <Flex direction="column" minH="100vh" >
      <PortalManager>
        <Navbar />
        <Box as="main" flex="1" width="100%">
          {/* El contenido de cada página se renderizará aquí */}
          <Outlet />
        </Box>
        <Footer />
      </PortalManager>    
    </Flex>
  );
};