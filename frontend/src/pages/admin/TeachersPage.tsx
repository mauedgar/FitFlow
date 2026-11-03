import { Box, Heading, Text, VStack } from '@chakra-ui/react';

/** No fabricated teacher/client records or nonfunctional mutation buttons. */
const TeachersPage = () => (
  <Box>
    <Heading as="h1" size="lg" mb={4}>Gestión de profesores</Heading>
    <VStack align="stretch" gap={3}>
      <Text>
        La administración de profesores todavía no está disponible desde esta vista.
      </Text>
      <Text color="gray.600">
        Esta página no muestra personas ficticias ni ofrece acciones de
        creación, edición o eliminación que aparenten modificar datos reales.
      </Text>
    </VStack>
  </Box>
);

export default TeachersPage;
