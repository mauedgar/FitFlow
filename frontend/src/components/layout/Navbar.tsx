import {
  Box,
  Flex,
  Heading,
  HStack,
  Link,
  IconButton,
  useDisclosure,
  Drawer,
  VStack,
  Spacer,
  Button,
  Container,
  Portal,
  CloseButton,
} from '@chakra-ui/react';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/useAuth';
import { LuMenu } from 'react-icons/lu';

export const Navbar = () => {
  const { open: isOpen, onOpen, onClose } = useDisclosure();
  const navigate = useNavigate();
  //Obtenemos el rol y la función logout del contexto
  const { userRole, logout } = useAuth();

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
      <Container maxW="80rem" px={4}>
        <Flex h={16} alignItems="center">
          <Heading size="md" asChild><RouterLink to="landing">FitFlow
                      </RouterLink></Heading>

          {/* ENLACES DE NAVEGACIÓN PARA DESKTOP */}
          <HStack as='nav' gap={5} ml={10} display={{ base: 'none', md: 'flex' }}>
            <Link asChild><RouterLink to="/">Inicio</RouterLink></Link>
            {userRole === 'client' && (
              <Link asChild><RouterLink to="/home">Mi Perfil
                              </RouterLink></Link>
            )}

            <Link asChild><RouterLink to="/classes">Clases
                          </RouterLink></Link>
          </HStack>

          <Spacer />

          {/* 3. BOTONES DINÁMICOS PARA DESKTOP */}
          <HStack gap={4} display={{ base: 'none', md: 'flex' }}>
            {userRole ? (
              // Si el usuario está logueado, muestra el botón de Logout
              <Button colorPalette="red" variant="solid" onClick={logoutUser}>
                Cerrar Sesión
              </Button>
            ) : (
              // Si no, muestra los botones de Login y Registro
              <>
                <Button colorPalette="teal" variant="solid" asChild><RouterLink to='/login'>Iniciar Sesión
                                  </RouterLink></Button>
                <Button colorPalette="teal" variant="solid" asChild><RouterLink to='/register'>Registrarse
                                  </RouterLink></Button>
              </>
            )}
          </HStack>

          {/* BOTÓN DE MENÚ HAMBURGUESA PARA MÓVIL */}
          <IconButton
            size="md"
            aria-label="Open Menu"
            display={{ base: 'flex', md: 'none' }}
            onClick={onOpen}><LuMenu /></IconButton>
        </Flex>
      </Container>

      {/* MENÚ LATERAL (DRAWER) PARA MÓVIL */}
      <Drawer.Root placement='end' open={isOpen} onOpenChange={e => {
        if (!e.open) {
          onClose();
        }
      }}>
        <Portal>

          <Drawer.Backdrop />
          <Drawer.Positioner>
            <Drawer.Content bg="gray.800" color="white">
              <Drawer.CloseTrigger asChild>
                <CloseButton aria-label="Cerrar menú" size="sm" position="absolute" top="2" right="2" />
              </Drawer.CloseTrigger>
              <Drawer.Header borderBottomWidth="1px"><Drawer.Title>Menú</Drawer.Title></Drawer.Header>
              <Drawer.Body>
                <VStack gap={4} align="stretch" mt={4}>
                  <Link asChild><RouterLink to="/" onClick={onClose}>Inicio</RouterLink></Link>
                  {userRole === 'client' && (
                  <Link asChild><RouterLink to="/home" onClick={onClose}>
                    Mi Perfil
                  </RouterLink></Link>
                  )}
                  <Link asChild><RouterLink to="/classes" onClick={onClose}>Clases</RouterLink></Link>
                  <Spacer />

                  {/* 5. BOTONES DINÁMICOS PARA MÓVIL */}
                  {userRole ? (
                    // Si el usuario está logueado
                    <Button
                      colorPalette="red"
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
                      <Button colorPalette="teal" variant="solid" w="100%" onClick={() => handleDrawerNavigate('/login')}>
                        Iniciar Sesión
                      </Button>
                      <Button colorPalette="teal" variant="outline" w="100%" onClick={() => handleDrawerNavigate('/register')}>
                        Registrarse
                      </Button>
                    </>
                  )}
                </VStack>
              </Drawer.Body>
            </Drawer.Content>
          </Drawer.Positioner>

        </Portal>
      </Drawer.Root>
    </Box>
  );
};
