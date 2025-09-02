import { 
  Box, 
  Flex, 
  Heading, 
  HStack, 
  Link, 
  IconButton, 
  useDisclosure,
  Drawer,
  DrawerOverlay,
  DrawerContent,
  DrawerHeader,
  DrawerBody,
  VStack,
  Spacer,
  Button,
  Container,
  DrawerCloseButton
} from '@chakra-ui/react';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { HamburgerIcon } from '@chakra-ui/icons';
import { useAuth } from '../../context/AuthContext';

export const Navbar = () => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const navigate = useNavigate();
  //Obtenemos el rol y la función logout del contexto
  const { rol, logout } = useAuth();

  // --- Handlers ---  

  const handleDrawerNavigate = (path: string) => {
    onClose(); // Cierra la UI primero
    setTimeout(() => {
      navigate(path); // Navega después de un pequeño retardo
    }, 150);
    };
  const logoutUser = () => {
    logout();
    navigate('/login');
  };
  
  return (
    <Box bg="gray.800" color="white" width="100%" position="sticky" top="0" zIndex="sticky">
      <Container maxW="container.xl" px={4}>
        <Flex h={16} alignItems="center">
          <Heading as={RouterLink} to="landing" size="md">
            FitFlow
          </Heading>

          {/* ENLACES DE NAVEGACIÓN PARA DESKTOP */}
          <HStack as='nav' spacing={5} ml={10} display={{ base: 'none', md: 'flex' }}>
            <Link as={RouterLink} to="/">Inicio</Link>
            {rol === 'client' && (
              <Link as={RouterLink} to="/home">
                Mi Perfil
              </Link>
            )}
            
            <Link as={RouterLink} to="/classes">
                Clases
            </Link>            
          </HStack>

          <Spacer />

          {/* 3. BOTONES DINÁMICOS PARA DESKTOP */}
          <HStack spacing={4} display={{ base: 'none', md: 'flex' }}>
            {rol ? (
              // Si el usuario está logueado, muestra el botón de Logout
              <Button colorScheme="red" variant="solid" onClick={logoutUser}>
                Cerrar Sesión
              </Button>
            ) : (
              // Si no, muestra los botones de Login y Registro
              <>
                <Button as = {RouterLink} to='/login' colorScheme="teal" variant="solid"> 
                  Iniciar Sesión
                </Button>
                <Button as = {RouterLink} to='/register' colorScheme="teal" variant="solid">
                  Registrarse
                </Button>
              </>
            )}
          </HStack>

          {/* BOTÓN DE MENÚ HAMBURGUESA PARA MÓVIL */}
          <IconButton
            size="md"
            icon={<HamburgerIcon />}
            aria-label="Open Menu"
            display={{ base: 'flex', md: 'none' }}
            onClick={onOpen}
          />
        </Flex>
      </Container>

      {/* MENÚ LATERAL (DRAWER) PARA MÓVIL */}
      <Drawer placement="right" onClose={onClose} isOpen={isOpen}>
        <DrawerOverlay />
        <DrawerContent bg="gray.800" color="white">
          <DrawerCloseButton />
          <DrawerHeader borderBottomWidth="1px">Menú</DrawerHeader>
          <DrawerBody>
            <VStack spacing={4} align="stretch" mt={4}>
              <Link onClick={() => handleDrawerNavigate('/')}>Inicio</Link>
              {rol === 'client' && (
              <Link onClick={() => handleDrawerNavigate('/home')}>
                Mi Perfil
              </Link>
              )}
              <Link onClick={() => handleDrawerNavigate('/classes')}>Clases</Link>                            
              <Spacer />

              {/* 5. BOTONES DINÁMICOS PARA MÓVIL */}
              {rol ? (
                // Si el usuario está logueado
                <Button
                  colorScheme="red"
                  w="100%"
                  onClick={() => {
                    onClose(); // Primero cierra la UI
                    setTimeout(logoutUser, 150); // Luego, con un retardo, ejecuta la lógica de la app
                  }}
                >
                  Cerrar Sesión
                </Button>
              ) : (
                // Si no está logueado
                <>
                  <Button colorScheme="teal" variant="solid" w="100%" onClick={() => handleDrawerNavigate('/login')}>
                    Iniciar Sesión
                  </Button>
                  <Button colorScheme="teal" variant="outline" w="100%" onClick={() => handleDrawerNavigate('/register')}>
                    Registrarse
                  </Button>
                </>
              )}
            </VStack>
          </DrawerBody>
        </DrawerContent>
      </Drawer>
    </Box>
  );
};