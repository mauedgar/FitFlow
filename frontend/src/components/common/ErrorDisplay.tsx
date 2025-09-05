import React from 'react';
import {
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Box,
} from '@chakra-ui/react';

interface ErrorDisplayProps {
  message: string;
}

const ErrorDisplay: React.FC<ErrorDisplayProps> = ({ message }) => {
  return (
    <Box my={4}>
      <Alert status="error" borderRadius="md">
        <AlertIcon />
        <AlertTitle mr={2}>¡Ocurrió un error!</AlertTitle>
        <AlertDescription>{message}</AlertDescription>
      </Alert>
    </Box>
  );
};

export default ErrorDisplay;