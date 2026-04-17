import { Box, VStack, Heading, Divider, Icon, HStack, Text } from '@chakra-ui/react';
import { NavLink as RouterNavLink } from 'react-router-dom';
import {
  FiHome,
  FiUsers,
  FiBriefcase,
  FiClipboard,
  FiBookOpen,
  FiBarChart2,
  FiCalendar,
  FiSettings,
  FiDollarSign,
} from 'react-icons/fi';


// Estructura de navegación del sidebar
const sidebarLinks = [
  { label: 'Dashboard', to: '/admin', icon: FiHome, end: true },
  { label: 'Clientes', to: '/admin/clients', icon: FiUsers },
  { label: 'Profesores', to: '/admin/teachers', icon: FiBriefcase },
  { label: 'Clases', to: '/admin/classes', icon: FiClipboard },
  { label: 'Reservas', to: '/admin/bookings', icon: FiBookOpen },
  { separator: true },
  { label: 'Informes', to: '/admin/reports', icon: FiBarChart2 },
  { label: 'Calendario', to: '/admin/calendar', icon: FiCalendar },
  { separator: true },
  { label: 'Herramientas', to: '/admin/tools', icon: FiSettings },
  { label: 'Facturación', to: '/admin/billing', icon: FiDollarSign },
];

const AdminSideBar = () => {
  const activeLinkStyle = {
    backgroundColor: '#319795', // teal.600
    color: 'white',
    fontWeight: 'bold',
  };

  return (
    <Box
      as="nav"
      bg="gray.800"
      color="white"
      w={{ base: 'full', md: '250px' }}
      h="full"
      p={4}
    >
      <Heading size="md" mb={6} color="teal.300">
        FitFlow Admin
      </Heading>

      <VStack align="stretch" spacing={1}>
        {sidebarLinks.map((link, index) => {
          // Renderizar separador
          if (link.separator) {
            return <Divider key={`separator-${index}`} my={3} borderColor="gray.600" />;
          }

          return (
            <Box
              key={link.to!}
              as={RouterNavLink}
              to={link.to!}
              end={link.end}
              style={({ isActive }: { isActive: boolean }) =>
                isActive ? activeLinkStyle : undefined
              }
              p={3}
              borderRadius="md"
              _hover={{ bg: 'gray.700' }}
              transition="all 0.2s"
            >
              <HStack spacing={3}>
                <Icon as={link.icon} />
                <Text fontSize="sm" fontWeight="medium">
                  {link.label}
                </Text>
              </HStack>
            </Box>
          );
        })}
      </VStack>
    </Box>
  );
};

export default AdminSideBar;