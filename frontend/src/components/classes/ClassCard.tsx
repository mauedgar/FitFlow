import React from 'react';
import {
  Card,
  CardHeader,
  CardBody,
  CardFooter,
  Heading,
  Text,
  Flex,
  Badge,
  VStack,
  HStack,
  Icon,
  StackDivider,
  Image, // Importamos Image para el fondo visual
} from '@chakra-ui/react';
import { FaUserGraduate, FaClock } from 'react-icons/fa';
import { type GymClass } from '../../types'; // Asumo que esta es la ruta correcta

interface ClassCardProps {
  gymClass: GymClass; // Renombrado para mayor claridad (gymClass vs classInfo)
  onClick?: () => void; // Prop opcional para manejar el click en la Fase 2
}

// --- Helpers de Presentación ---
// Abstraemos la lógica de formato para mantener el JSX limpio.

const getTeacherNames = (teachers: GymClass['teachers']): string => {
  if (!teachers || teachers.length === 0) {
    return 'Instructor por confirmar';
  }
  return teachers.map(t => `${t.name} ${t.surname}`).join(', ');
};

const formatClassTime = (schedule: string, duration: number): string => {
  const startTime = new Date(schedule).toLocaleTimeString('es-AR', {
    hour: '2-digit',
    minute: '2-digit',
  });
  return `${startTime} hs - ${duration} min`;
};

const difficultyColorScheme: Record<string, string> = {
  Principante: 'green',
  Intermedio: 'orange',
  Avanzado: 'red',
};

// --- Componente Principal ---

const ClassCard: React.FC<ClassCardProps> = ({ gymClass, onClick }) => {
  const { name, description, difficulty, teachers, schedule, duration_minutes } = gymClass;

  return (
    // 1. Usamos el componente <Card> semántico. Viene con estilos base.
    <Card
      direction="column"
      overflow="hidden"
      variant="outline" // Un estilo sutil
      transition="all 0.2s ease-in-out"
      _hover={{
        transform: 'scale(1.02)', // Un efecto de zoom sutil
        boxShadow: 'xl',
        cursor: onClick ? 'pointer' : 'default',
      }}
      onClick={onClick}
      size="md"
    >
      {/* 2. Añadimos una imagen como pediste, que mejora mucho el atractivo visual */}
      <Image
        objectFit="cover"
        maxH="150px"
        src={`https://picsum.photos/400/200/?fitness,${name}`}
        alt={`Imagen de la clase ${name}`}
      />

      {/* 3. <CardHeader> para el título y metadatos principales. */}
      <CardHeader>
        <Flex justify="space-between" align="center" gap={4}>
          <Heading size="md" noOfLines={2}>
            {name}
          </Heading>
          <Badge
            flexShrink={0} // Evita que el badge se encoja si el título es largo
            colorScheme={difficultyColorScheme[difficulty] || 'gray'}
            variant="solid" // Un estilo más prominente
            borderRadius="full"
            px={3}
          >
            {difficulty}
          </Badge>
        </Flex>
      </CardHeader>

      {/* 4. <CardBody> para el contenido principal, como la descripción. */}
      <CardBody py={0}>
        <Text fontSize="sm" color="gray.600" noOfLines={3}>
          {description}
        </Text>
      </CardBody>

      {/* 5. <CardFooter> para información secundaria y acciones. */}
      <CardFooter>
        <VStack
          divider={<StackDivider borderColor="gray.200" />} // ¡Un separador elegante!
          spacing={3}
          align="stretch"
          w="100%"
        >
          <HStack color="gray.700">
            <Icon as={FaUserGraduate} w={4} h={4} />
            <Text fontSize="sm" fontWeight="medium">{getTeacherNames(teachers)}</Text>
          </HStack>
          <HStack color="gray.700">
            <Icon as={FaClock} w={4} h={4} />
            <Text fontSize="sm" fontWeight="medium">{formatClassTime(schedule, duration_minutes)}</Text>
          </HStack>
        </VStack>
      </CardFooter>
    </Card>
  );
};

export default ClassCard;