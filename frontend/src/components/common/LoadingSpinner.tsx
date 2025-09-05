import React from 'react';
import { Box, Spinner, Text, VStack } from '@chakra-ui/react';

const LoadingSpinner: React.FC = () => {
  return (
    <Box textAlign="center" py={10} px={6}>
      <VStack spacing={4}>
        <Spinner
          thickness="4px"
          speed="0.65s"
          emptyColor="gray.200"
          color="blue.500"
          size="xl"
        />
        <Text fontSize="lg" color="gray.600">Cargando clases...</Text>
      </VStack>
    </Box>
  );
};

export default LoadingSpinner;