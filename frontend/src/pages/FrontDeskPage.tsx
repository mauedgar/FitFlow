import React, { useState } from 'react';
import {
  Badge,
  Box,
  Button,
  Card,
  CardBody,
  Container,
  Heading,
  HStack,
  SimpleGrid,
  Spinner,
  Text,
  VStack,
  useToast,
} from '@chakra-ui/react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { BookingStatus } from '../types';
import frontDeskService, {
  type FrontDeskBooking,
  type FrontDeskSession,
} from '../services/frontDeskService';

const formatTime = (value: string) =>
  new Date(value).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

const FrontDeskPage: React.FC = () => {
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const toast = useToast();
  const queryClient = useQueryClient();

  const dayQuery = useQuery({
    queryKey: ['frontDesk', 'today'],
    queryFn: frontDeskService.getToday,
  });

  const bookingsQuery = useQuery({
    queryKey: ['frontDesk', 'bookings', selectedSessionId],
    queryFn: () => frontDeskService.getSessionBookings(selectedSessionId!),
    enabled: !!selectedSessionId,
  });

  const checkInMutation = useMutation({
    mutationFn: ({ sessionId, bookingId }: { sessionId: string; bookingId: string }) =>
      frontDeskService.checkIn(sessionId, bookingId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['frontDesk', 'today'] });
      if (selectedSessionId) {
        queryClient.invalidateQueries({
          queryKey: ['frontDesk', 'bookings', selectedSessionId],
        });
      }
      toast({
        title: 'Check-in registrado',
        status: 'success',
        duration: 2500,
        isClosable: true,
      });
    },
    onError: () => {
      toast({
        title: 'No se pudo registrar el check-in',
        status: 'error',
        duration: 3500,
        isClosable: true,
      });
    },
  });

  const renderSession = (session: FrontDeskSession) => (
    <Card key={session.id} variant="outline">
      <CardBody>
        <VStack spacing={3} align="stretch">
          <HStack justify="space-between" align="start">
            <Box>
              <Heading size="sm">{session.gym_class_name}</Heading>
              <Text fontSize="sm">{session.teacher_full_name}</Text>
            </Box>
            <Badge colorScheme={session.is_full ? 'red' : 'green'}>
              {session.available_spots} cupos
            </Badge>
          </HStack>
          <Text fontSize="sm">
            {formatTime(session.starts_at)} - {formatTime(session.ends_at)}
          </Text>
          <Text fontSize="sm">
            Reservas: {session.current_bookings_count}/{session.capacity_snapshot}
          </Text>
          <Button
            size="sm"
            variant={selectedSessionId === session.id ? 'solid' : 'outline'}
            onClick={() => setSelectedSessionId(session.id)}
          >
            Ver reservas
          </Button>
        </VStack>
      </CardBody>
    </Card>
  );

  const renderBooking = (booking: FrontDeskBooking) => {
    if (!selectedSessionId) {
      return null;
    }

    const canCheckIn = booking.status === BookingStatus.CONFIRMED;

    return (
      <Card key={booking.id} variant="outline">
        <CardBody>
          <HStack justify="space-between" align="center">
            <Box>
              <Text fontWeight="semibold">{booking.client_name}</Text>
              <Text fontSize="sm" color="gray.600">{booking.client_email}</Text>
              <Badge mt={2}>{booking.status}</Badge>
            </Box>
            <Button
              colorScheme="teal"
              size="sm"
              isDisabled={!canCheckIn}
              isLoading={checkInMutation.isPending}
              onClick={() =>
                checkInMutation.mutate({
                  sessionId: selectedSessionId,
                  bookingId: booking.id,
                })
              }
            >
              Check-in
            </Button>
          </HStack>
        </CardBody>
      </Card>
    );
  };

  return (
    <Container maxW="container.xl" py={8}>
      <VStack spacing={8} align="stretch">
        <Box>
          <Heading size="lg">Front Desk</Heading>
          <Text color="gray.600">Operacion diaria: sesiones, reservas y check-in.</Text>
        </Box>

        <Box>
          <Heading size="md" mb={4}>Sesiones de hoy</Heading>
          {dayQuery.isLoading && <Spinner />}
          {dayQuery.isError && <Text color="red.500">No se pudieron cargar las sesiones.</Text>}
          {dayQuery.data && dayQuery.data.sessions.length === 0 && (
            <Text>No hay sesiones programadas para hoy.</Text>
          )}
          {dayQuery.data && dayQuery.data.sessions.length > 0 && (
            <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={4}>
              {dayQuery.data.sessions.map(renderSession)}
            </SimpleGrid>
          )}
        </Box>

        <Box>
          <Heading size="md" mb={4}>Reservas de la sesion</Heading>
          {!selectedSessionId && <Text>Selecciona una sesion para operar sus reservas.</Text>}
          {selectedSessionId && bookingsQuery.isLoading && <Spinner />}
          {selectedSessionId && bookingsQuery.isError && (
            <Text color="red.500">No se pudieron cargar las reservas.</Text>
          )}
          {selectedSessionId && bookingsQuery.data && bookingsQuery.data.length === 0 && (
            <Text>La sesion no tiene reservas.</Text>
          )}
          {selectedSessionId && bookingsQuery.data && (
            <VStack spacing={3} align="stretch">
              {bookingsQuery.data.map(renderBooking)}
            </VStack>
          )}
        </Box>
      </VStack>
    </Container>
  );
};

export default FrontDeskPage;
