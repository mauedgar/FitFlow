import { Box, Grid, GridItem, Heading, Text, VStack, Image } from '@chakra-ui/react';

const activitiesData = [
    // ... (datos de las actividades que te proporcioné anteriormente)
    {
        title: 'Yoga & Meditación',
        description: 'Encuentra tu centro y mejora tu flexibilidad en nuestras clases para todos los niveles.',
        image: 'https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?q=80&w=1200'
    },
    {
        title: 'CrossFit de Alta Intensidad',
        description: 'Supera tus límites con entrenamientos funcionales y desafiantes.',
        image: 'https://images.unsplash.com/photo-1517836357463-d25dfeac3438?q=80&w=1200'
    },
    {
        title: 'Spinning Energético',
        description: 'Quema calorías y fortalece tu sistema cardiovascular al ritmo de la mejor música.',
        image: 'https://images.unsplash.com/photo-1594882645126-14020914d58d?q=80&w=1200'
    },
    {
        title: 'Boxeo y Artes Marciales',
        description: 'Aprende técnicas de defensa personal mientras mejoras tu condición física.',
        image: 'https://images.unsplash.com/photo-1593352222389-68128b9df32a?q=80&w=1200'
    },
    {
        title: 'Musculación y Pesas',
        description: 'Desarrolla tu fuerza y tonifica tu cuerpo en nuestra completa área de pesas.',
        image: 'https://images.unsplash.com/photo-1581009137042-c552e485697a?q=80&w=1200'
    },
];

const ActivitiesSection = () => {
  return (
    <Box bg="gray.50" py={{ base: 16, md: 24 }}>
      <Grid
        templateColumns={{ base: '1fr', lg: '1fr 1.5fr' }}
        gap={{ base: 8, lg: 16 }}
        maxWidth="1280px"
        mx="auto"
        px={{ base: 4, md: 8 }}
      >
        <GridItem position={{ lg: 'sticky' }} top="100px" alignSelf="start" height="auto">
          <VStack spacing={6} align="start" textAlign={{ base: "center", lg: "left" }}>
            <Heading as="h2" size={{ base: '2xl', md: '3xl' }} color="gray.800">
              Todas las actividades que buscas.
            </Heading>
            <Text fontSize="xl" color="gray.600">
              Desde entrenamientos de alta intensidad hasta clases de relajación, en FitFlow tenemos algo para ti. Explora nuestras opciones y encuentra tu pasión.
            </Text>
          </VStack>
        </GridItem>

        <GridItem>
          <VStack spacing={8}>
            {activitiesData.map((activity, index) => (
              <Box
                key={index}
                bg="white"
                borderRadius="lg"
                boxShadow="md"
                overflow="hidden"
                width="full"
                transition="transform 0.2s, box-shadow 0.2s"
                _hover={{ transform: 'scale(1.02)', boxShadow: 'xl' }}
              >
                <Image src={activity.image} alt={activity.title} objectFit="cover" height="250px" width="full" />
                <Box p={6}>
                  <Heading as="h3" size="lg" mb={2}>{activity.title}</Heading>
                  <Text color="gray.600">{activity.description}</Text>
                </Box>
              </Box>
            ))}
          </VStack>
        </GridItem>
      </Grid>
    </Box>
  );
};

export default ActivitiesSection;