import { Avatar, Button, Flex, HStack, Icon, Menu, Spacer, Text, Portal } from '@chakra-ui/react';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/useAuth';
import {
  FiHome,
  FiUsers,
  FiLogOut,
  FiBriefcase,
} from 'react-icons/fi';
import { LuChevronDown } from 'react-icons/lu';

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
      <Button variant="ghost" colorPalette="teal" size="md" asChild><RouterLink to="/admin"><Icon asChild><FiHome /></Icon>Dashboard
                        </RouterLink></Button>

      <Spacer />

      {/* MENÚS CRUD Y GESTIÓN */}
      <HStack gap="2" overflowX="auto">
        {adminMenus.map((menu) => (
          <Menu.Root key={menu.label} navigate={({ value }) => navigate(value)}>
            <Menu.Trigger asChild><Button variant="ghost" size="sm" minW="max-content">
                <HStack gap="1">
                  <Icon asChild><menu.icon /></Icon>
                  <Text>{menu.label}</Text>
                </HStack>
                <LuChevronDown /></Button></Menu.Trigger>
            <Portal><Menu.Positioner><Menu.Content>
                  {menu.subitems.map((item) => (
                    <Menu.Item key={item.to} value={item.to} asChild><RouterLink to={item.to}>
                        <Icon asChild><item.icon /></Icon>{item.label}
                      </RouterLink></Menu.Item>
                  ))}
                </Menu.Content></Menu.Positioner></Portal>
          </Menu.Root>
        ))}
      </HStack>

      <Spacer />

      {/* PERFIL Y LOGOUT */}
      <Menu.Root>
        <Menu.Trigger asChild><Button variant="ghost" p={2} rounded="full">
            <HStack gap="2">
              <Avatar.Root size="sm"><Avatar.Fallback name={currentUser?.email || 'Admin'} /></Avatar.Root>
              <Text display={{ base: 'none', lg: 'block' }} fontSize="sm" fontWeight="medium">
                {currentUser?.email || 'Administrador'}
              </Text>
              <LuChevronDown />
            </HStack>
          </Button></Menu.Trigger>
        <Portal><Menu.Positioner><Menu.Content>
              <Menu.Item
                onSelect={handleLogout}
                color="red.500"
                value='logout'>
                <Icon asChild><FiLogOut /></Icon>Cerrar Sesión
              </Menu.Item>
            </Menu.Content></Menu.Positioner></Portal>
      </Menu.Root>
    </Flex>
  );
};

export default AdminNavBar;
