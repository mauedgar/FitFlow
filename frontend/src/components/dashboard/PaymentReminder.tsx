// src/components/dashboard/PaymentReminder.tsx
import React from 'react';
import { Alert, Box } from '@chakra-ui/react';

const PaymentReminder: React.FC = () => {
  // Esto vendría de tu API
  const daysUntilDue = 7;
  const hasPaymentDue = daysUntilDue <= 7;

  if (!hasPaymentDue) return null;

  return (
    <Alert.Root status="warning" borderRadius="md">
      <Alert.Indicator />
      <Box fontSize="sm">
        <Alert.Title>¡Cuota por vencer!</Alert.Title>
        <Alert.Description>
          Tu cuota vence en {daysUntilDue} días
        </Alert.Description>
      </Box>
    </Alert.Root>
  );
};

export default PaymentReminder;