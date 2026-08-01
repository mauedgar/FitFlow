// src/components/dashboard/DocumentReminder.tsx
import React from 'react';
import { Alert, AlertIcon, AlertTitle, AlertDescription, Box } from '@chakra-ui/react';

const DocumentReminder: React.FC = () => {
  // Esto vendría de tu API
  const hasMedicalCertificate = false;

  if (hasMedicalCertificate) return null;

  return (
    <Alert status="info" borderRadius="md">
      <AlertIcon />
      <Box fontSize="sm">
        <AlertTitle>Documentación</AlertTitle>
        <AlertDescription>
          Falta cargar revisión médica
        </AlertDescription>
      </Box>
    </Alert>
  );
};

export default DocumentReminder;