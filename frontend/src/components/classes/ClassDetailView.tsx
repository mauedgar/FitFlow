import React from 'react';
import {
  Box, Heading, Text, Badge, VStack, HStack, Icon, Divider,
  SimpleGrid
} from '@chakra-ui/react';
import { FaClock, FaTachometerAlt } from 'react-icons/fa';
// 1. Asegúrate de importar el tipo de dato que vas a recibir.
import { type GymClass, type ClassScheduleWithNextSession } from '../../types';
import ClassScheduleSection from './ClassScheduleSection'; // Nuevo subcomponente


// 2. DEFINE LA INTERFAZ DE PROPS: Este es el "manual de instrucciones".
// Le dice a TypeScript que este componente DEBE recibir una prop llamada 'gymClass'
// que sea del tipo 'GymClass'.
interface ClassDetailViewProps {
  gymClass: GymClass;
  onCloseModal?: () => void; // Para cerrar el modal después de reservar, si es necesario
}

// 3. APLICA LA INTERFAZ AL COMPONENTE: Usa React.FC<TuInterfazDeProps>
// y desestructura la prop 'gymClass' de los argumentos.
export const ClassDetailView: React.FC<ClassDetailViewProps> = ({ gymClass, onCloseModal }) => {  
  return (
    <VStack spacing={8} align="stretch">
      <Box>
        {/* Ahora puedes usar gymClass de forma segura, con autocompletado y type-checking */}
        <Heading as="h1" size="2xl">{gymClass.name}</Heading>
        <Text fontSize="xl" color="gray.500" mt={2}>{gymClass.description}</Text>
      </Box>

      <SimpleGrid columns={{ base: 1, md: 3 }} spacing={10}>
        <HStack>
          <Icon as={FaTachometerAlt} w={6} h={6} color="teal.500" />
          <Box>
            <Text fontSize="sm" color="gray.500">Dificultad</Text>
            <Badge colorScheme={gymClass.difficulty === "Principante" ? "green" : gymClass.difficulty === "Intermedio" ? "orange" : "red"} variant="solid" fontSize="md">{gymClass.difficulty}</Badge>
          </Box>
        </HStack>
        <HStack>
          <Icon as={FaClock} w={6} h={6} color="teal.500" />
          <Box>
            <Text fontSize="sm" color="gray.500">Duración</Text>
            <Text fontSize="lg" fontWeight="bold">{gymClass.duration_minutes} min</Text>
          </Box>
        </HStack>
      </SimpleGrid>

      <Divider />

      <Box>
        <Heading as="h2" size="lg" mb={4}>Horarios y Reservas</Heading>
        {gymClass.class_schedules && gymClass.class_schedules.length > 0 ? (
          <VStack spacing={6} align="stretch">
            {gymClass.class_schedules.map((schedule) => (
              <ClassScheduleSection
                key={schedule.id}
                classSchedule={schedule as ClassScheduleWithNextSession}
                gymClassName={gymClass.name} // Pasa el nombre para toasts
                onCloseModal={onCloseModal}
              />
            ))}
          </VStack>
        ) : (
          <Text>No hay horarios programados para esta clase.</Text>
        )}
      </Box>
    </VStack>
  );
};

// Si usas export default, asegúrate de que sea consistente.
export default ClassDetailView;