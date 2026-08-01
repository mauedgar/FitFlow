// src/components/dashboard/PaymentReminder.tsx
import React from 'react';
import { Alert, AlertIcon, AlertTitle, AlertDescription, Box } from '@chakra-ui/react';

const PaymentReminder: React.FC = () => {
  // Esto vendría de tu API
  const daysUntilDue = 7;
  const hasPaymentDue = daysUntilDue <= 7;

  if (!hasPaymentDue) return null;

  return (
    <Alert status="warning" borderRadius="md">
      <AlertIcon />
      <Box fontSize="sm">
        <AlertTitle>¡Cuota por vencer!</AlertTitle>
        <AlertDescription>
          Tu cuota vence en {daysUntilDue} días
        </AlertDescription>
      </Box>
    </Alert>
  );
};

export default PaymentReminder;