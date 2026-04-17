import React from 'react';
import {
  Box, Text, Button, Badge, useToast, Flex, Spacer,
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
  const toast     = useToast();
  const navigate  = useNavigate();
  const queryClient = useQueryClient();

  /* ---------------------------------------------------- */
  /* 1.  Datos de auth                                   */
  /* ---------------------------------------------------- */
  const { isAuthenticated, isClient, userBookings, isLoadingBookings, userRole } = useAuth();

  const userAlreadyBooked = userBookings?.some(
    (b) => b.class_session_id === classSession.id && b.status === BookingStatus.CONFIRMED,
  );

  /* ---------------------------------------------------- */
  /* 2.  Mutación para reservar la sesión                 */
  /* ---------------------------------------------------- */
  const bookSessionMutation = useMutation({
    mutationFn: (payload: BookingCreatePayload) => classService.createBooking(payload),
    onSuccess: () => {
      toast({
        title: '¡Reserva confirmada!',
        description: `Has reservado un cupo para ${classSession.class_schedule?.gym_class?.name ??'la clase'} el ${getFormattedDateTime(classSession.start_datetime)}.`,
        status: 'success',
        duration: 5000,
        isClosable: true,
      });
      // Re–frescar cache
      queryClient.invalidateQueries({ queryKey: ['classSessions'] });
      queryClient.invalidateQueries({ queryKey: ['myBookings'] });
      onCloseModal?.();
    },
    onError: (err: unknown) => {
      /*  evitamos any → casteamos solo si es AxiosError  */
      const axiosErr = err as AxiosError<{ detail?: string }>;
      const status   = axiosErr.response?.status;
      const msg      = axiosErr.response?.data?.detail || 'Error al procesar la reserva.';

      toast({
        title: 'Error de reserva',
        description: msg,
        status: 'error',
        duration: 5000,
        isClosable: true,
      });

      if (status === 401 || status === 403) navigate('/login');
    },
  });

  const handleBookClick = () => {
    if (!isAuthenticated) {
      toast({
        title: 'Inicia sesión',
        description: 'Debes iniciar sesión para reservar una clase.',
        status: 'info',
        duration: 3000,
        isClosable: true,
      });
      navigate('/login');
      return;
    }
    if (!isClient) {
      toast({
        title: 'Permiso denegado',
        description: 'Solo los clientes pueden reservar clases.',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    /*  👈  enviamos el objeto esperado por la API  */
    bookSessionMutation.mutate({ class_session_id: classSession.id });
  };

  /* ---------------------------------------------------- */
  /* 3.  Estado del botón                                 */
  /* ---------------------------------------------------- */
  const isFull        = classSession.available_spots <= 0;
  const isPast        = new Date(classSession.start_datetime) < new Date();
  const pendingReq    = bookSessionMutation.isPending || isLoadingBookings;

  const buttonDisabled = isPast || isFull || userAlreadyBooked || pendingReq || !isAuthenticated || !isClient;

  const buttonLabel = isPast
    ? 'Sesión finalizada'
    : userAlreadyBooked
    ? 'Reservado'
    : isFull
    ? 'Lleno'
    : 'Reservar Ahora';

  /* ---------------------------------------------------- */
  /* 4.  Render                                           */
  /* ---------------------------------------------------- */
  return (
    <Box p={4} borderWidth="1px" borderRadius="md" bg="white" shadow="sm">
      <Flex align="center" mb={2}>
        <Text fontSize="md" fontWeight="bold">
          {getFormattedDateTime(classSession.start_datetime)}
        </Text>
        <Spacer />
        {!isPast && (
          <Badge
            colorScheme={
              isFull ? 'red' : classSession.available_spots <= 3 ? 'orange' : 'green'
            }
            fontSize="sm"
          >
            {isFull ? 'Lleno' : `${classSession.available_spots} cupos`}
          </Badge>
        )}
      </Flex>

      <Text fontSize="sm" color="gray.600" mb={4}>
        Duración: {classSession.class_schedule.gym_class?.duration_minutes ?? 'N/A'} min
      </Text>

      <Button
        colorScheme="teal"
        size="sm"
        w="100%"
        onClick={handleBookClick}
        isDisabled={buttonDisabled}
        isLoading={pendingReq}
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