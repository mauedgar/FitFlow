import { Box, VStack, Heading, Icon, HStack, Text } from '@chakra-ui/react';
import { NavLink as RouterNavLink } from 'react-router-dom';
import {
  FiHome,
  FiUsers,
  FiBriefcase,
} from 'react-icons/fi';


// Estructura de navegación del sidebar
const sidebarLinks = [
  { label: 'Dashboard', to: '/admin', icon: FiHome, end: true },
  { label: 'Clientes', to: '/admin/clients', icon: FiUsers },
  { label: 'Profesores', to: '/admin/teachers', icon: FiBriefcase },
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

      <VStack align="stretch" gap={1}>
        {sidebarLinks.map((link) => {
          return (
            <Box
              key={link.to}
              p={3}
              borderRadius="md"
              _hover={{ bg: 'gray.700' }}
              transition="all 0.2s"
              asChild><RouterNavLink to={link.to} end={link.end} style={({ isActive }) => isActive ? activeLinkStyle : undefined}>
                <HStack gap={3}>
                  <Icon as={link.icon} />
                  <Text fontSize="sm" fontWeight="medium">
                    {link.label}
                  </Text>
                </HStack>
              </RouterNavLink></Box>
          );
        })}
      </VStack>
    </Box>
  );
};

export default AdminSideBar;
