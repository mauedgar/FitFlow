import { Box, Text } from '@chakra-ui/react';

export const Footer: React.FC =() => {
  return (
    <Box as="footer" bg="gray.700" color="gray.200" py={4} mt="auto">
      <Text textAlign="center">
        &copy; {new Date().getFullYear()} FitFlow. Todos los derechos reservados.
      </Text>
    </Box>
  );
};