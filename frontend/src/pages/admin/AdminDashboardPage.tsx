import { Box, Heading, Text } from '@chakra-ui/react';

const AdminDashboardPage = () => {
  return (
    <Box>
      <Heading as="h1" mb={4}>Bienvenido al Panel de Administración</Heading>
      <Text>Selecciona una opción en el menú lateral para comenzar a gestionar el gimnasio.</Text>
    </Box>
  );
};

export default AdminDashboardPage;