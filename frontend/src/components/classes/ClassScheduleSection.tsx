import { toaster } from '../ui/toaster-store';
import React from 'react';
import {
  Box, Heading, Text, VStack, HStack, Icon,
   Flex, Button, Alert, Badge,
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
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { isAuthenticated, isClient, userRole } = useAuth();

  /* ------------------------------------------------------------------
     2. Mutación para reservar (sin cambios)
  -------------------------------------------------------------------*/
  const bookScheduleMutation = useMutation({
    mutationFn: (payload: BookingCreatePayload) => classService.createBooking(payload),
    onSuccess: () => {
      toaster.create({
        title: '¡Cupo reservado!',
        description: `Has reservado tu cupo recurrente para ${gymClassName}. Revisa tu calendario.`,
        type: 'success', duration: 5000, closable: true,
      });
      queryClient.invalidateQueries({ queryKey: ['myBookings'] });
      queryClient.invalidateQueries({ queryKey: ['gymClasses'] });
      onCloseModal?.();
    },
    onError: (err: unknown) => {
      const axiosErr = err as AxiosError<{ detail?: string }>;
      const msg = axiosErr.response?.data?.detail || 'Error al procesar la reserva.';
      toaster.create({ title: 'No se pudo completar la reserva', description: msg, type: 'error', duration: 6000, closable: true });
      if (axiosErr.response?.status === 401) navigate('/login');
    },
  });

  /* ------------------------------------------------------------------
     3. Lógica de UI para la Badge y el Botón (Nueva Estrategia)
  -------------------------------------------------------------------*/
  const nextSession = classSchedule?.next_upcoming_session;

  const isAvailable = !!nextSession;
  const referenceCapacityReached = isAvailable && nextSession.available_spots <= 0;
  // Pre-calculamos las propiedades de la Badge para un render más limpio
  const getBadgeProps = () => {
    if (!isAvailable) {
      return { text: 'No disponible por ahora', colorScheme: 'gray' };
    }
    if (referenceCapacityReached) {
      return { text: 'Referencia alcanzada · reservas abiertas', colorScheme: 'purple' };
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
  const buttonDisabled = pendingMutation || !isAuthenticated || !isClient || !isAvailable;
  const buttonLabel = 'Reservar';

  const handleBookClick = () => {
    if (!isAuthenticated) { navigate('/login'); return; }
    if (!isClient) {
      toaster.create({ title: 'Acción no permitida', description: 'Solo los clientes pueden reservar.', type: 'warning', duration: 3000, closable: true });
      return;
    }
    bookScheduleMutation.mutate({ class_schedule_id: classSchedule.id, status: BookingStatus.CONFIRMED });
  };

  /* ------------------------------------------------------------------
     4. Helpers y valores para el Render
  -------------------------------------------------------------------*/
  const teacher = classSchedule.teacher;
  const startTime = classSchedule.start_time?.substring(0, 5) ?? '??:??';
  const durationMinutes = classSchedule.duration_minutes;
  const endTime = (() => {
    if (!classSchedule.start_time) return '??:??';
    const [hour, minute] = classSchedule.start_time.split(':').map(Number);
    if (!Number.isFinite(hour) || !Number.isFinite(minute)) return '??:??';
    const totalMinutes = ((hour * 60) + minute + durationMinutes) % (24 * 60);
    const endHour = Math.floor(totalMinutes / 60).toString().padStart(2, '0');
    const endMinute = (totalMinutes % 60).toString().padStart(2, '0');
    return `${endHour}:${endMinute}`;
  })();
  const days = classSchedule.rrule;

  if (!teacher) {
    return <Alert.Root status="warning" my={4}><Alert.Indicator /><Alert.Content><Alert.Description>Falta información del instructor.</Alert.Description></Alert.Content></Alert.Root>;
  }

  /* ------------------------------------------------------------------
     5. Render final
  -------------------------------------------------------------------*/
  return (
    <Box p={4} borderWidth="1px" borderRadius="lg" bg="white" shadow="sm">
      <Flex direction={{ base: 'column', md: 'row' }} justify="space-between" align={{ base: 'stretch', md: 'center' }}>
        {/* --- LADO IZQUIERDO: Información del Horario --- */}
        <VStack align="stretch" gap={2} mb={{ base: 4, md: 0 }}>
          <Heading as="h4" size="sm">{gymClassName} – Horario Recurrente</Heading>
          <HStack><Icon as={FaCalendarWeek} color="blue.500" /><Text fontWeight="medium">Días: {days}</Text></HStack>
          <HStack><Icon as={FaHourglassHalf} color="blue.500" /><Text>Horario: {startTime} – {endTime} hs</Text></HStack>
          <HStack><Icon as={FaUserGraduate} color="blue.500" /><Text>Instructor: {teacher.first_name ?? ''} {teacher.last_name ?? ''}</Text></HStack>
        </VStack>

        {/* --- LADO DERECHO: Acciones de Reserva --- */}
        <VStack gap={2} align={{ base: 'stretch', md: 'flex-end' }}>
          {/* ⭐ NUEVA BADGE DE ESTADO */}
          <Badge colorPalette={badgeProps.colorScheme} variant="subtle" px={3} py={1} borderRadius="md">
            {badgeProps.text}
          </Badge>

          <Button
            colorPalette="teal"
            w={{ base: '100%', md: 'auto' }}
            onClick={handleBookClick}
            disabled={buttonDisabled}
            loading={pendingMutation}
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
