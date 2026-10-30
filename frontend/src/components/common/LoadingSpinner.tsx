import React from 'react';
import { Box, Spinner, Text, VStack } from '@chakra-ui/react';

const LoadingSpinner: React.FC = () => {
  return (
    <Box textAlign="center" py={10} px={6}>
      <VStack gap={4}>
        <Spinner
          borderWidth="4px"
          animationDuration="0.65s"
          color="blue.500"
          size="xl"
        />
        <Text fontSize="lg" color="gray.600">Cargando clases...</Text>
      </VStack>
    </Box>
  );
};

export default LoadingSpinner;
