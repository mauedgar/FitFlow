import { Box, Container, Heading, Text, Grid, GridItem, Card, CardBody, VStack } from '@chakra-ui/react';
const HomePage = () => {
  return (
    <Container maxW="container.xl" py={10}>
      <VStack spacing={8} align="stretch">
        <Box>
          <Heading mb={2}>
            
          </Heading>
          <Text color="gray.600">Bienvenido de vuelta</Text>
        </Box>

        <Grid templateColumns="repeat(auto-fit, minmax(250px, 1fr))" gap={6}>
          <GridItem>
            <Card>
              <CardBody>
                <Heading size="md" mb={2}>Mis Clases</Heading>
                <Text>3 clases esta semana</Text>
              </CardBody>
            </Card>
          </GridItem>

          <GridItem>
            <Card>
              <CardBody>
                <Heading size="md" mb={2}>Progreso</Heading>
                <Text>75% completado</Text>
              </CardBody>
            </Card>
          </GridItem>

          <GridItem>
            <Card>
              <CardBody>
                <Heading size="md" mb={2}>Próxima Clase</Heading>
                <Text>Yoga - Mañana 10:00 AM</Text>
              </CardBody>
            </Card>
          </GridItem>
        </Grid>
      </VStack>
    </Container>
  );
};
export default HomePage;