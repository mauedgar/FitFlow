// src/components/admin/layout/AdminNavBar.tsx

import {
  Avatar,
  Button,
  Flex,
  HStack,
  Icon,
  Menu,
  MenuButton,
  MenuDivider,
  MenuItem,
  MenuList,
  Spacer,
  Text,
} from '@chakra-ui/react';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
// Importamos los iconos que usaremos
import { FiHome, FiUsers, FiLogOut, FiBriefcase, FiClipboard } from 'react-icons/fi';
import { ChevronDownIcon } from '@chakra-ui/icons';

const AdminNavBar: React.FC = () => {
  const { rol, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login'); // Redirigir al login después de cerrar sesión
  };

  return (
    <Flex
      as="header"
      align="center"
      justify="space-between"
      w="100%"
      px="4"
      py="2"
      bg="white"
      borderBottomWidth="1px"
      borderColor="gray.200"
      h="64px" // Altura fija para la barra de navegación
    >
      {/* SECCIÓN IZQUIERDA: Botón Home */}
      <Button
        as={RouterLink}
        to="/admin" // La ruta raíz del admin es el dashboard
        leftIcon={<Icon as={FiHome} />}
        variant="ghost"
        colorScheme="teal"
      >
        Dashboard
      </Button>

      <Spacer />

      {/* SECCIÓN CENTRAL: Menús de CRUD */}
      <HStack spacing="4">
        {/* Menú Clientes */}
        <Menu>
          <MenuButton as={Button} rightIcon={<ChevronDownIcon />}>
            Clientes
          </MenuButton>
          <MenuList>
            <MenuItem as={RouterLink} to="/admin/clients" icon={<Icon as={FiUsers} />}>
              Ver Clientes
            </MenuItem>
            {/* Puedes añadir más opciones como "Añadir Cliente" aquí */}
          </MenuList>
        </Menu>

        {/* Menú Profesores */}
        <Menu>
          <MenuButton as={Button} rightIcon={<ChevronDownIcon />}>
            Profesores
          </MenuButton>
          <MenuList>
            <MenuItem as={RouterLink} to="/admin/teachers" icon={<Icon as={FiBriefcase} />}>
              Ver Profesores
            </MenuItem>
          </MenuList>
        </Menu>

        {/* Menú Clases */}
        <Menu>
          <MenuButton as={Button} rightIcon={<ChevronDownIcon />}>
            Clases
          </MenuButton>
          <MenuList>
            <MenuItem as={RouterLink} to="/admin/CruClasses" icon={<Icon as={FiClipboard} />}>
              Gestionar Clases
            </MenuItem>
          </MenuList>
        </Menu>

        {/* Puedes añadir los menús de Facturación e Informes aquí en el futuro */}
      </HStack>

      <Spacer />

      {/* SECCIÓN DERECHA: Perfil y Logout */}
      <Menu>
        <MenuButton as={Button} variant="ghost" p={2} rounded="full">
          <HStack>
            <Avatar size="sm" name="Admin" /> {/* Puedes poner el nombre del usuario aquí */}
            <Text display={{ base: 'none', md: 'block' }} fontSize="sm" fontWeight="medium">
              Admin
            </Text>
            <ChevronDownIcon />
          </HStack>
        </MenuButton>
        <MenuList>
          <MenuItem>Mi Perfil</MenuItem>
          <MenuDivider />
          <MenuItem
            onClick={handleLogout}
            color="red.500" // Color distintivo para una acción destructiva/final
            icon={<Icon as={FiLogOut} />}
          >
            Cerrar Sesión
          </MenuItem>
        </MenuList>
      </Menu>
    </Flex>
  );
};

export default AdminNavBar;
