import { toaster } from '../ui/toaster-store';
/* eslint-disable @typescript-eslint/no-explicit-any */
import React from 'react';
import {
  Box, Text, Button, Badge,  Flex, Spacer,
} from '@chakra-ui/react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { type ClassSession, BookingStatus, type BookingCreatePayload } from '../../types';
import classService from '../../services/classService';
import { getFormattedDateTime } from '../../utils/formatters';
import { useAuth } from '../../context/useAuth';
import { useNavigate } from 'react-router-dom';
import type { AxiosError } from 'axios';

interface ClassSessionCardProps {
  classSession: ClassSession;
  onCloseModal?: () => void;
}

const ClassSessionCard: React.FC<ClassSessionCardProps> = ({
  classSession,
  onCloseModal,
}) => {
  const navigate  = useNavigate();
  const queryClient = useQueryClient();

  /* ---------------------------------------------------- */
  /* 1.  Datos de auth                                   */
  /* ---------------------------------------------------- */
  const { isAuthenticated, isClient, userBookings, isLoadingBookings, userRole } = useAuth();

  const userAlreadyBooked = userBookings?.some(
    (b) =>
      b.status === BookingStatus.CONFIRMED &&
      b.starts_at === classSession.starts_at &&
      b.gym_class_name === (classSession.class_schedule?.gym_class?.name ?? ''),
  );

  /* ---------------------------------------------------- */
  /* 2.  Mutación para reservar la sesión                 */
  /* ---------------------------------------------------- */
  const bookSessionMutation = useMutation({
    mutationFn: (payload: BookingCreatePayload) => classService.createBooking(payload),
    onSuccess: () => {
      toaster.create({
        title: '¡Reserva confirmada!',
        description: `Has reservado un cupo para ${classSession.class_schedule?.gym_class?.name ?? 'la clase'} el ${getFormattedDateTime(classSession.starts_at)}.`,
        type: 'success',
        duration: 5000,
        closable: true,
      });
      // Re–frescar cache
      queryClient.invalidateQueries({ queryKey: ['classSessions'] });
      queryClient.invalidateQueries({ queryKey: ['myBookings'] });
      onCloseModal?.();
    },
    onError: (err: any) => {
      /*  evitamos any → casteamos solo si es AxiosError  */
      const axiosErr = err as AxiosError<any>;
      const status   = axiosErr.response?.status;
      const data      = axiosErr.response?.data;
      const rawErrorMessage = JSON.stringify(data);

      toaster.create({
        title: 'Error de reserva',
        description: rawErrorMessage,
        type: 'error',
        duration: 10000,
        closable: true,
      });

      if (status === 401 || status === 403) navigate('/login');
    },
  });

  const handleBookClick = () => {
    if (!isAuthenticated) {
      toaster.create({
        title: 'Inicia sesión',
        description: 'Debes iniciar sesión para reservar una clase.',
        type: 'info',
        duration: 3000,
        closable: true,
      });
      navigate('/login');
      return;
    }
    if (!isClient) {
      toaster.create({
        title: 'Permiso denegado',
        description: 'Solo los clientes pueden reservar clases.',
        type: 'warning',
        duration: 3000,
        closable: true,
      });
      return;
    }

    /*  👈  enviamos el objeto esperado por la API  */
    bookSessionMutation.mutate({ class_session_id: classSession.id,status: BookingStatus.CONFIRMED  });
  };

  /* ---------------------------------------------------- */
  /* 3.  Estado del botón                                 */
  /* ---------------------------------------------------- */
  const referenceCapacityReached = classSession.available_spots <= 0;
  const isPast        = new Date(classSession.starts_at) < new Date();
  const pendingReq    = bookSessionMutation.isPending || isLoadingBookings;

  const buttonDisabled = isPast || userAlreadyBooked || pendingReq || !isAuthenticated || !isClient;

  const buttonLabel = isPast
    ? 'Sesión finalizada'
    : userAlreadyBooked
    ? 'Reservado'
    : 'Reservar Ahora';

  /* ---------------------------------------------------- */
  /* 4.  Render                                           */
  /* ---------------------------------------------------- */
  return (
    <Box p={4} borderWidth="1px" borderRadius="md" bg="white" shadow="sm">
      <Flex align="center" mb={2}>
        <Text fontSize="md" fontWeight="bold">
          {getFormattedDateTime(classSession.starts_at)}
        </Text>
        <Spacer />
        {!isPast && (
          <Badge
            colorPalette={
              referenceCapacityReached ? 'purple' : classSession.available_spots <= 3 ? 'orange' : 'green'
            }
            fontSize="sm"
          >
            {referenceCapacityReached ? 'Referencia alcanzada · reservas abiertas' : `${classSession.available_spots} cupos de referencia`}
          </Badge>
        )}
      </Flex>

      <Text fontSize="sm" color="gray.600" mb={4}>
        Duración: {classSession.class_schedule.gym_class?.duration_minutes ?? 'N/A'} min
      </Text>

      <Button
        colorPalette="teal"
        size="sm"
        w="100%"
        onClick={handleBookClick}
        disabled={buttonDisabled}
        loading={pendingReq}
      >
        {buttonLabel}
      </Button>

      {!isAuthenticated && (
        <Text fontSize="xs" color="gray.500" mt={1} textAlign="center">
          Inicia sesión para reservar
        </Text>
      )}
      {isAuthenticated && !isClient && userRole && (
        <Text fontSize="xs" color="gray.500" mt={1} textAlign="center">
          Tu rol ({userRole}) no puede reservar clases.
        </Text>
      )}
    </Box>
  );
};

export default ClassSessionCard;