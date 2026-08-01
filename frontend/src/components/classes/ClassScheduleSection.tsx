import React from 'react';
import {
  Box, Heading, Text, VStack, HStack, Icon,
  Flex, Button, useToast, Alert, AlertIcon, Badge,
} from '@chakra-ui/react';
import { FaUserGraduate, FaCalendarWeek, FaHourglassHalf } from 'react-icons/fa';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import type { AxiosError } from 'axios';

import {    
  BookingStatus,
  type BookingCreatePayload, 
  type ClassScheduleWithNextSession 
} from '../../types';
import classService from '../../services/classService';
import { useAuth } from '../../context/useAuth';
import { getFormattedDate } from '../../utils/formatters';

interface ClassScheduleSectionProps {
  classSchedule: ClassScheduleWithNextSession;
  gymClassName: string;
  onCloseModal?: () => void;
}

const ClassScheduleSection: React.FC<ClassScheduleSectionProps> = ({
  classSchedule,
  gymClassName,
  onCloseModal,
}) => {
  /* ------------------------------------------------------------------
     1. Hooks esenciales
  -------------------------------------------------------------------*/
  const toast = useToast();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { isAuthenticated, isClient, userRole } = useAuth();

  /* ------------------------------------------------------------------
     2. Mutación para reservar (sin cambios)
  -------------------------------------------------------------------*/
  const bookScheduleMutation = useMutation({
    mutationFn: (payload: BookingCreatePayload) => classService.createBooking(payload),
    onSuccess: () => {
      toast({
        title: '¡Cupo reservado!',
        description: `Has reservado tu cupo recurrente para ${gymClassName}. Revisa tu calendario.`,
        status: 'success', duration: 5000, isClosable: true,
      });
      queryClient.invalidateQueries({ queryKey: ['myBookings'] });
      queryClient.invalidateQueries({ queryKey: ['gymClasses'] });
      onCloseModal?.();
    },
    onError: (err: unknown) => {
      const axiosErr = err as AxiosError<{ detail?: string }>;
      const msg = axiosErr.response?.data?.detail || 'Error al procesar la reserva.';
      toast({ title: 'No se pudo completar la reserva', description: msg, status: 'error', duration: 6000, isClosable: true });
      if (axiosErr.response?.status === 401) navigate('/login');
    },
  });

  /* ------------------------------------------------------------------
     3. Lógica de UI para la Badge y el Botón (Nueva Estrategia)
  -------------------------------------------------------------------*/
  const nextSession = classSchedule?.next_upcoming_session;

  const isAvailable = !!nextSession; 
  const isFull = isAvailable ? nextSession.available_spots <= 0 : true;

  // Pre-calculamos las propiedades de la Badge para un render más limpio
  const getBadgeProps = () => {
    if (!isAvailable) {
      return { text: 'No disponible por ahora', colorScheme: 'gray' };
    }
    if (isFull) {
      return { text: 'Próxima fecha sin cupos', colorScheme: 'red' };
    }
    
    const nextDate = getFormattedDate(new Date(nextSession.starts_at));
    const text = `Próximo inicio: ${nextDate}`;
    
    if (nextSession.available_spots <= 3) {
      return { text, colorScheme: 'orange' };
    }
    return { text, colorScheme: 'green' };
  };

  const badgeProps = getBadgeProps();

  // Lógica de deshabilitación del botón
  const pendingMutation = bookScheduleMutation.isPending;
  const buttonDisabled = pendingMutation || !isAuthenticated || !isClient || !isAvailable || isFull;
  const buttonLabel = 'Reservar'; // Texto fijo

  const handleBookClick = () => {
    if (!isAuthenticated) { navigate('/login'); return; }
    if (!isClient) {
      toast({ title: 'Acción no permitida', description: 'Solo los clientes pueden reservar.', status: 'warning', duration: 3000, isClosable: true });
      return;
    }
    bookScheduleMutation.mutate({ class_schedule_id: classSchedule.id, status: BookingStatus.CONFIRMED });
  };

  /* ------------------------------------------------------------------
     4. Helpers y valores para el Render
  -------------------------------------------------------------------*/
  const dayNames = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
  const getDaysOfWeekString = (days: number[] = []) => days.map((d) => dayNames[d] ?? '¿?').join(', ');
  const teacher = classSchedule.teacher;
  const startTime = classSchedule.start_time?.substring(0, 5) ?? '??:??';
  const endTime = classSchedule.duration_minutes?.substring(0, 5) ?? '??:??';
  const days = getDaysOfWeekString(classSchedule.days_of_week);

  if (!teacher) {
    return <Alert status="warning" my={4}><AlertIcon />Falta información del instructor.</Alert>;
  }

  /* ------------------------------------------------------------------
     5. Render final
  -------------------------------------------------------------------*/
  return (
    <Box p={4} borderWidth="1px" borderRadius="lg" bg="white" shadow="sm">
      <Flex direction={{ base: 'column', md: 'row' }} justify="space-between" align={{ base: 'stretch', md: 'center' }}>
        {/* --- LADO IZQUIERDO: Información del Horario --- */}
        <VStack align="stretch" spacing={2} mb={{ base: 4, md: 0 }}>
          <Heading as="h4" size="sm">{gymClassName} – Horario Recurrente</Heading>
          <HStack><Icon as={FaCalendarWeek} color="blue.500" /><Text fontWeight="medium">Días: {days}</Text></HStack>
          <HStack><Icon as={FaHourglassHalf} color="blue.500" /><Text>Horario: {startTime} – {endTime} hs</Text></HStack>
          <HStack><Icon as={FaUserGraduate} color="blue.500" /><Text>Instructor: {teacher.first_name ?? ''} {teacher.last_name ?? ''}</Text></HStack>
        </VStack>

        {/* --- LADO DERECHO: Acciones de Reserva --- */}
        <VStack spacing={2} align={{ base: 'stretch', md: 'flex-end' }}>
          {/* ⭐ NUEVA BADGE DE ESTADO */}
          <Badge colorScheme={badgeProps.colorScheme} variant="subtle" px={3} py={1} borderRadius="md">
            {badgeProps.text}
          </Badge>

          <Button
            colorScheme="teal"
            w={{ base: '100%', md: 'auto' }}
            onClick={handleBookClick}
            isDisabled={buttonDisabled}
            isLoading={pendingMutation}
          >
            {buttonLabel}
          </Button>

          {isAuthenticated && !isClient && userRole && (
            <Text fontSize="xs" color="gray.500" textAlign={{ base: 'center', md: 'right' }}>
              Tu rol ({userRole}) no puede reservar.
            </Text>
          )}
        </VStack>
      </Flex>
      
      {/* --- SECCIÓN DE SESIONES FUTURAS (COMENTADA) --- */}
      {/* 
        <Divider my={4} />
        TODO: Sprint X - Habilitar la vista de sesiones individuales futuras.
              Esta sección requeriría una query separada para traer las ClassSession
              generadas para este ClassSchedule.
        <Heading as="h4" size="sm" mb={3}>
          Próximas Sesiones Programadas
        </Heading>
        <Text fontSize="sm" color="gray.600">
          Funcionalidad pendiente de implementación.
        </Text>
      */}
    </Box>
  );
};

export default ClassScheduleSection;
