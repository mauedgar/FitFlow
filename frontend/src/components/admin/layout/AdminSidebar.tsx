import { Box, VStack, Heading, Divider } from '@chakra-ui/react';
// 1. Importamos NavLink con un alias para mayor claridad
import { NavLink as RouterNavLink } from 'react-router-dom';

const AdminSideBar = () => {
  // 2. Definimos los estilos para el estado activo.
  //    Estos son estilos de CSS-in-JS estándar que React entiende.
  const activeLinkStyle = {
    backgroundColor: '#38B2AC', // Usamos el valor hexadecimal de 'teal.500' para el objeto style
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
      <Heading size="md" mb={6}>Admin Panel</Heading>
      <VStack align="stretch" spacing={2}>
        {/* 3. Usamos Box como decorador de estilos para RouterNavLink */}
        <Box
          as={RouterNavLink}
          to="/admin"
          end // 'end' asegura que solo coincida con /admin exacto
          // 4. Pasamos la función a la prop 'style' de NavLink.
          //    Tipamos 'isActive' como boolean para que TypeScript esté contento.
          style={({ isActive }: { isActive: boolean }) =>
            isActive ? activeLinkStyle : undefined
          }
          // 5. Aplicamos los estilos de Chakra UI directamente en el Box
          p={2}
          borderRadius="md"
          _hover={{ bg: 'gray.700' }}
        >
          Dashboard
        </Box>

        {/* Repetimos el mismo patrón para los demás enlaces */}
        <Box
          as={RouterNavLink}
          to="/admin/clients"
          style={({ isActive }: { isActive: boolean }) =>
            isActive ? activeLinkStyle : undefined
          }
          p={2}
          borderRadius="md"
          _hover={{ bg: 'gray.700' }}
        >
          Clientes
        </Box>

        <Box
          as={RouterNavLink}
          to="/admin/teachers"
          style={({ isActive }: { isActive: boolean }) =>
            isActive ? activeLinkStyle : undefined
          }
          p={2}
          borderRadius="md"
          _hover={{ bg: 'gray.700' }}
        >
          Profesores
        </Box>

        <Box
          as={RouterNavLink}
          to="/admin/classes"
          style={({ isActive }: { isActive: boolean }) =>
            isActive ? activeLinkStyle : undefined
          }
          p={2}
          borderRadius="md"
          _hover={{ bg: 'gray.700' }}
        >
          Clases
        </Box>
        
        <Divider my={4} />

        <Box
          as={RouterNavLink}
          to="/admin/billing"
          style={({ isActive }: { isActive: boolean }) =>
            isActive ? activeLinkStyle : undefined
          }
          p={2}
          borderRadius="md"
          _hover={{ bg: 'gray.700' }}
        >
          Facturación (Próximamente)
        </Box>
      </VStack>
    </Box>
  );
};

export default AdminSideBar;