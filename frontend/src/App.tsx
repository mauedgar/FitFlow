import { Box, Heading, Button, VStack, Text } from '@chakra-ui/react'

function App() {
  return (
    // Box es como un <div> pero con superpoderes de estilo
    <Box p={8} textAlign="center">
      <VStack spacing={6}> {/* VStack apila elementos verticalmente con un espacio de 6 */}
        <Heading as="h1" size="2xl" color="teal.500">
          Bienvenido a FitFlow
        </Heading>
        <Text fontSize="xl">Tu compañero de fitness definitivo.</Text>
        <Button colorScheme="teal" size="lg">
          Empezar ahora
        </Button>
      </VStack>
    </Box>
  )
}
export default App;

