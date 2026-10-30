// src/components/dashboard/DocumentReminder.tsx
import React from 'react';
import { Alert, Box } from '@chakra-ui/react';

const DocumentReminder: React.FC = () => {
  // Esto vendría de tu API
  const hasMedicalCertificate = false;

  if (hasMedicalCertificate) return null;

  return (
    <Alert.Root status="info" borderRadius="md">
      <Alert.Indicator />
      <Box fontSize="sm">
        <Alert.Title>Documentación</Alert.Title>
        <Alert.Description>
          Falta cargar revisión médica
        </Alert.Description>
      </Box>
    </Alert.Root>
  );
};

export default DocumentReminder;