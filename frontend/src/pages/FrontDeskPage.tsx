import React, { useState } from 'react';
import {
  Badge,
  Box,
  Button,
  Card,
  CardBody,
  Container,
  FormControl,
  FormLabel,
  Heading,
  HStack,
  Input,
  SimpleGrid,
  Spinner,
  Text,
  VStack,
  useToast,
} from '@chakra-ui/react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { BookingStatus } from '../types';
import { businessTimeLabel } from '../utils/businessTimezone';
import frontDeskService, {
  type FrontDeskBooking,
  type FrontDeskClientLookup,
  type FrontDeskSession,
} from '../services/frontDeskService';

const FrontDeskPage: React.FC = () => {
  const [documentNumber, setDocumentNumber] = useState('');
  const [client, setClient] = useState<FrontDeskClientLookup | null>(null);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [preparedBooking, setPreparedBooking] = useState<FrontDeskBooking | null>(null);
  const toast = useToast();
  const queryClient = useQueryClient();

  // A document lookup is the entry point; session selection cannot identify a client.
  const lookupMutation = useMutation({
    mutationFn: (document: string) => frontDeskService.getClientByDocument(document),
    onSuccess: (resolved) => {
      setClient(resolved);
      setSelectedSessionId(null);
      setPreparedBooking(null);
    },
    onError: () => {
      setClient(null);
      setSelectedSessionId(null);
      setPreparedBooking(null);
      toast({ title: 'No se pudo identificar al cliente por documento', status: 'error', duration: 3500, isClosable: true });
    },
  });

  const dayQuery = useQuery({
    queryKey: ['frontDesk', 'today'],
    queryFn: frontDeskService.getToday,
    enabled: client !== null,
  });

  const bookingsQuery = useQuery({
    queryKey: ['frontDesk', 'bookings', selectedSessionId],
    queryFn: () => frontDeskService.getSessionBookings(selectedSessionId!),
    enabled: client !== null && selectedSessionId !== null,
  });

  const fallbackMutation = useMutation({
    mutationFn: ({ sessionId, clientId }: { sessionId: string; clientId: string }) =>
      frontDeskService.ensureFallbackBooking(sessionId, clientId),
    onSuccess: (result, request) => {
      if (selectedSessionId === request.sessionId && client?.id === request.clientId) {
        setPreparedBooking(result.booking);
      }
      void queryClient.invalidateQueries({ queryKey: ['frontDesk', 'bookings', request.sessionId] });
      void queryClient.invalidateQueries({ queryKey: ['frontDesk', 'today'] });
      toast({
        title: result.created ? 'Reserva ordinaria creada' : 'Reserva existente localizada',
        description: 'El check-in requiere una acción explícita separada.',
        status: 'success',
        duration: 3500,
        isClosable: true,
      });
    },
    onError: () => {
      toast({
        title: 'No se pudo crear la reserva',
        description: 'El backend debe validar la membresía y elegibilidad.',
        status: 'error',
        duration: 4000,
        isClosable: true,
      });
    },
  });

  const checkInMutation = useMutation({
    mutationFn: ({ sessionId, bookingId }: { sessionId: string; bookingId: string }) =>
      frontDeskService.checkIn(sessionId, bookingId),
    onSuccess: (booking, request) => {
      if (selectedSessionId === request.sessionId) setPreparedBooking(booking);
      void queryClient.invalidateQueries({ queryKey: ['frontDesk', 'today'] });
      void queryClient.invalidateQueries({ queryKey: ['frontDesk', 'bookings', request.sessionId] });
      toast({ title: 'Check-in registrado', status: 'success', duration: 2500, isClosable: true });
    },
    onError: () => {
      toast({ title: 'No se pudo registrar el check-in', status: 'error', duration: 3500, isClosable: true });
    },
  });

  const isBusy = lookupMutation.isPending || fallbackMutation.isPending || checkInMutation.isPending;
  const ownBooking = bookingsQuery.data?.find(
    (booking) => booking.client_id === client?.id && booking.status !== BookingStatus.CANCELLED,
  ) ?? (preparedBooking?.client_id === client?.id ? preparedBooking : null);

  const selectSession = (sessionId: string) => {
    setSelectedSessionId(sessionId);
    setPreparedBooking(null);
  };

  const renderSession = (session: FrontDeskSession) => (
    <Card key={session.id} variant="outline">
      <CardBody>
        <VStack spacing={3} align="stretch">
          <HStack justify="space-between" align="start">
            <Box>
              <Heading size="sm">{session.gym_class_name}</Heading>
              <Text fontSize="sm">{session.teacher_full_name ?? 'Sin docente asignado'}</Text>
            </Box>
            <Badge colorScheme="gray">{session.available_spots} cupos de referencia</Badge>
          </HStack>
          <Text fontSize="sm">
            {businessTimeLabel(session.starts_at)} - {businessTimeLabel(session.ends_at)}
          </Text>
          <Text fontSize="sm">
            Reservas: {session.current_bookings_count}/{session.capacity_snapshot}
          </Text>
          <Button
            size="sm"
            isDisabled={isBusy}
            variant={selectedSessionId === session.id ? 'solid' : 'outline'}
            onClick={() => selectSession(session.id)}
          >
            Seleccionar sesión
          </Button>
        </VStack>
      </CardBody>
    </Card>
  );

  return (
    <Container maxW="container.xl" py={8}>
      <VStack spacing={8} align="stretch">
        <Box>
          <Heading size="lg">Front Desk</Heading>
          <Text color="gray.600">Identifica primero al cliente y opera reservas y check-in ordinarios.</Text>
        </Box>

        <Box as="form" onSubmit={(event: React.FormEvent) => {
          event.preventDefault();
          if (documentNumber.trim() && !isBusy) {
            setClient(null);
            setSelectedSessionId(null);
            setPreparedBooking(null);
            lookupMutation.mutate(documentNumber.trim());
          }
        }}>
          <VStack align="stretch" spacing={3}>
            <FormControl>
              <FormLabel>Número de documento</FormLabel>
              <Input
                value={documentNumber}
                onChange={(event) => {
                  setDocumentNumber(event.target.value);
                  setClient(null);
                  setSelectedSessionId(null);
                  setPreparedBooking(null);
                }}
                placeholder="Documento exacto del cliente"
              />
            </FormControl>
            <Button type="submit" colorScheme="teal" isLoading={lookupMutation.isPending}
              isDisabled={!documentNumber.trim() || isBusy}>
              Buscar cliente
            </Button>
          </VStack>
        </Box>

        {client && (
          <Card variant="outline">
            <CardBody>
              <Text fontWeight="bold">{client.full_name}</Text>
              <Text fontSize="sm">{client.document_number} · {client.email}</Text>
              <Text fontSize="sm" color="gray.600">Cliente identificado; la búsqueda no concede elegibilidad.</Text>
            </CardBody>
          </Card>
        )}

        {client && (
          <Box>
            <Heading size="md" mb={4}>Sesiones de hoy</Heading>
            {dayQuery.isLoading && <Spinner />}
            {dayQuery.isError && <Text color="red.500">No se pudieron cargar las sesiones.</Text>}
            {dayQuery.data?.sessions.length === 0 && <Text>No hay sesiones programadas para hoy.</Text>}
            {dayQuery.data && dayQuery.data.sessions.length > 0 && (
              <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={4}>
                {dayQuery.data.sessions.map(renderSession)}
              </SimpleGrid>
            )}
          </Box>
        )}

        {client && (
          <Box>
            <Heading size="md" mb={4}>Reserva y check-in del cliente</Heading>
            {!selectedSessionId && <Text>Selecciona una sesión para el cliente identificado.</Text>}
            {selectedSessionId && bookingsQuery.isLoading && <Spinner />}
            {selectedSessionId && bookingsQuery.isError && (
              <Text color="red.500">No se pudieron consultar las reservas. No se crearán reservas sin verificar.</Text>
            )}
            {selectedSessionId && bookingsQuery.isSuccess && (
              <VStack align="stretch" spacing={3}>
                {ownBooking && (
                  <Card variant="outline">
                    <CardBody>
                      <Text fontWeight="semibold">{ownBooking.client_name}</Text>
                      <Badge mt={2}>{ownBooking.status}</Badge>
                    </CardBody>
                  </Card>
                )}
                {!ownBooking && (
                  <Button colorScheme="teal" variant="outline"
                    isLoading={fallbackMutation.isPending}
                    isDisabled={isBusy}
                    onClick={() => fallbackMutation.mutate({
                      sessionId: selectedSessionId, clientId: client.id,
                    })}>
                    Crear reserva ordinaria
                  </Button>
                )}
                {ownBooking?.status === BookingStatus.CONFIRMED && (
                  <Button colorScheme="teal"
                    isLoading={checkInMutation.isPending}
                    isDisabled={isBusy}
                    onClick={() => checkInMutation.mutate({
                      sessionId: selectedSessionId, bookingId: ownBooking.id,
                    })}>
                    Registrar check-in
                  </Button>
                )}
                {ownBooking && ownBooking.status !== BookingStatus.CONFIRMED && (
                  <Text fontSize="sm">La reserva no está confirmada para un nuevo check-in.</Text>
                )}
                <Text fontSize="sm" color="gray.600">
                  Crear una reserva no registra asistencia. El check-in usa el comando ordinario y separado.
                </Text>
              </VStack>
            )}
          </Box>
        )}
      </VStack>
    </Container>
  );
};

export default FrontDeskPage;
