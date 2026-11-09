import React from 'react';
import { Button, Container, Heading, Text, VStack } from '@chakra-ui/react';
import { Link as RouterLink } from 'react-router-dom';

// This is a bounded, role-guarded landing. Do not imply that teacher
// attendance/assigned-session operations are implemented by this screen.
const TeacherLandingPage: React.FC = () => (
  <Container maxW="64rem" py={10}>
    <VStack align="stretch" gap={5}>
      <Heading size="lg">Portal docente</Heading>
      <Text>Tu sesión está verificada como docente.</Text>
      <Text color="gray.600">
        La gestión de sesiones asignadas y asistencia requiere una
        implementación específica. Esta vista no habilita esas operaciones.
      </Text>
      <Button colorPalette="teal" asChild>
        <RouterLink to="/classes">Consultar clases</RouterLink>
      </Button>
    </VStack>
  </Container>
);

export default TeacherLandingPage;
