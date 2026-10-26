import {
  Avatar,
  Button,
  Flex,
  HStack,
  Icon,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  Spacer,
  Text,
} from '@chakra-ui/react';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/useAuth';
import {
  FiHome,
  FiUsers,
  FiLogOut,
  FiBriefcase,
} from 'react-icons/fi';
import { ChevronDownIcon } from '@chakra-ui/icons';

// Configuración de menús para fácil mantenimiento y escalabilidad
const adminMenus = [
  {
    label: "Clientes",
    icon: FiUsers,
    subitems: [
      { label: "Ver Clientes", to: "/admin/clients", icon: FiUsers },
    ]
  },
  {
    label: "Profesores",
    icon: FiBriefcase,
    subitems: [
      { label: "Ver Profesores", to: "/admin/teachers", icon: FiBriefcase },
    ]
  },
];

const AdminNavBar: React.FC = () => {
  const { currentUser, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
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
      h="64px"
      boxShadow="sm"
    >
      {/* DASHBOARD BUTTON */}
      <Button
        as={RouterLink}
        to="/admin"
        leftIcon={<Icon as={FiHome} />}
        variant="ghost"
        colorScheme="teal"
        size="md"
      >
        Dashboard
      </Button>

      <Spacer />

      {/* MENÚS CRUD Y GESTIÓN */}
      <HStack spacing="2" overflowX="auto">
        {adminMenus.map((menu) => (
          <Menu key={menu.label}>
            <MenuButton
              as={Button}
              rightIcon={<ChevronDownIcon />}
              variant="ghost"
              size="sm"
              minW="max-content"
            >
              <HStack spacing="1">
                <Icon as={menu.icon} />
                <Text>{menu.label}</Text>
              </HStack>
            </MenuButton>
            <MenuList>
              {menu.subitems.map((item) => (
                <MenuItem
                  key={item.to}
                  as={RouterLink}
                  to={item.to}
                  icon={<Icon as={item.icon} />}
                >
                  {item.label}
                </MenuItem>
              ))}
            </MenuList>
          </Menu>
        ))}
      </HStack>

      <Spacer />

      {/* PERFIL Y LOGOUT */}
      <Menu>
        <MenuButton as={Button} variant="ghost" p={2} rounded="full">
          <HStack spacing="2">
            <Avatar size="sm" name={currentUser?.email || 'Admin'} />
            <Text display={{ base: 'none', lg: 'block' }} fontSize="sm" fontWeight="medium">
              {currentUser?.email || 'Administrador'}
            </Text>
            <ChevronDownIcon />
          </HStack>
        </MenuButton>
        <MenuList>
          <MenuItem
            onClick={handleLogout}
            color="red.500"
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
