import { useRef, useState } from 'react';
import { Avatar, Box, Button, Drawer, Flex, HStack, Icon, Menu, Portal, Spacer, Text, VStack } from '@chakra-ui/react';
import { Link as RouterLink, NavLink as RouterNavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/useAuth';
import { FiHome, FiUsers, FiLogOut, FiBriefcase, FiMenu } from 'react-icons/fi';
import { LuChevronDown } from 'react-icons/lu';

const adminLinks = [
  { label: 'Dashboard', to: '/admin', icon: FiHome, end: true },
  { label: 'Clientes', to: '/admin/clients', icon: FiUsers },
  { label: 'Profesores', to: '/admin/teachers', icon: FiBriefcase },
];

const AdminNavBar: React.FC = () => {
  const { currentUser, logout } = useAuth();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuTrigger = useRef<HTMLButtonElement>(null);

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
      minW={0}
      gap={{ base: 1, md: 2 }}
      px={{ base: 2, md: 4 }}
      py="2"
      bg="white"
      borderBottomWidth="1px"
      borderColor="gray.200"
      h="64px"
      boxShadow="sm"
    >
      <Drawer.Root open={menuOpen} onOpenChange={({ open }) => setMenuOpen(open)}
        placement="start" finalFocusEl={() => menuTrigger.current}>
        <Drawer.Trigger asChild>
          <Button ref={menuTrigger} display={{ base: 'inline-flex', md: 'none' }}
            variant="ghost" aria-label="Menú" aria-expanded={menuOpen}>
            <Icon as={FiMenu} />
            <Text>Menú</Text>
          </Button>
        </Drawer.Trigger>
        <Portal>
          <Drawer.Backdrop />
          <Drawer.Positioner>
            <Drawer.Content maxW="min(280px, 100vw)" bg="gray.800" color="white">
              <Drawer.Header>
                <Drawer.Title>Secciones de administración</Drawer.Title>
              </Drawer.Header>
              <Drawer.Body>
                <VStack as="nav" aria-label="Secciones de administración" align="stretch" gap={1}>
                  {adminLinks.map((link) => (
                    <Box key={link.to} asChild _focusVisible={{ outline: '3px solid', outlineColor: 'teal.200', outlineOffset: '2px' }}>
                      <RouterNavLink to={link.to} end={link.end}
                        onClick={() => setMenuOpen(false)}
                        style={({ isActive }) => ({
                          display: 'flex', alignItems: 'center', gap: '12px', padding: '12px',
                          borderRadius: '6px', backgroundColor: isActive ? '#2C7A7B' : 'transparent',
                          color: 'white', fontWeight: isActive ? 'bold' : 'normal',
                        })}>
                        <Icon as={link.icon} />{link.label}
                      </RouterNavLink>
                    </Box>
                  ))}
                </VStack>
              </Drawer.Body>
              <Drawer.CloseTrigger aria-label="Cerrar menú" color="white" />
            </Drawer.Content>
          </Drawer.Positioner>
        </Portal>
      </Drawer.Root>

      <Button variant="ghost" colorPalette="teal" size="md" asChild display={{ base: 'none', md: 'inline-flex' }}>
        <RouterLink to="/admin" aria-label="Dashboard">
          <Icon as={FiHome} />
          <Text>Dashboard</Text>
        </RouterLink>
      </Button>
      <Spacer />

      <Menu.Root>
        <Menu.Trigger asChild><Button variant="ghost" p={2} rounded="full" flexShrink={0} aria-label="Menú de perfil">
            <HStack gap="2">
              <Avatar.Root size="sm"><Avatar.Fallback name={currentUser?.email || 'Admin'} /></Avatar.Root>
              <Text display={{ base: 'none', lg: 'block' }} fontSize="sm" fontWeight="medium">
                {currentUser?.email || 'Administrador'}
              </Text>
              <LuChevronDown />
            </HStack>
          </Button></Menu.Trigger>
        <Portal><Menu.Positioner><Menu.Content>
              <Menu.Item onSelect={handleLogout} color="red.500" value="logout">
                <Icon as={FiLogOut} />Cerrar Sesión
              </Menu.Item>
            </Menu.Content></Menu.Positioner></Portal>
      </Menu.Root>
    </Flex>
  );
};

export default AdminNavBar;
