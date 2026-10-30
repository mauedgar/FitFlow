import { toaster } from '../components/ui/toaster-store';
import React, { useRef, useState } from 'react';
import {
  Badge,
  Box,
  Button,
  Card,
  Container,
  Heading,
  HStack,
  Input,
  SimpleGrid,
  Spinner,
  Text,
  VStack,
  Field,
} from '@chakra-ui/react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { BookingStatus } from '../types';
import { businessTimeLabel } from '../utils/businessTimezone';
import { isCurrentLookupIntent, nextLookupIntent, type LookupIntent } from '../utils/frontDeskLookupIntent';
import frontDeskService, {
  type FrontDeskBooking,
  type FrontDeskClientLookup,
  type FrontDeskSession,
} from '../services/frontDeskService';

const FrontDeskPage: React.FC = () => {
  const [documentNumber, setDocumentNumber] = useState('');
  // Revision increments at each edit and at each submitted request.
  // Ref updates synchronously so a late response cannot reidentify an old client.
  const lookupIntentRef = useRef<LookupIntent>({ revision: 0, document: '' });
  const [client, setClient] = useState<FrontDeskClientLookup | null>(null);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [preparedBooking, setPreparedBooking] = useState<FrontDeskBooking | null>(null);
  const queryClient = useQueryClient();

  // A document lookup is the entry point; session selection cannot identify a client.
  const lookupMutation = useMutation({
    mutationFn: (intent: LookupIntent) => frontDeskService.getClientByDocument(intent.document),
    onSuccess: (resolved, intent) => {
      if (!isCurrentLookupIntent(lookupIntentRef.current, intent)) return;
      setClient(resolved);
      setSelectedSessionId(null);
      setPreparedBooking(null);
    },
    onError: (_error, intent) => {
      if (!isCurrentLookupIntent(lookupIntentRef.current, intent)) return;
      setClient(null);
      setSelectedSessionId(null);
      setPreparedBooking(null);
      toaster.create({ title: 'No se pudo identificar al cliente por documento', type: 'error', duration: 3500, closable: true });
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
      toaster.create({
        title: result.created ? 'Reserva ordinaria creada' : 'Reserva existente localizada',
        description: 'El check-in requiere una acción explícita separada.',
        type: 'success',
        duration: 3500,
        closable: true,
      });
    },
    onError: () => {
      toaster.create({
        title: 'No se pudo crear la reserva',
        description: 'El backend debe validar la membresía y elegibilidad.',
        type: 'error',
        duration: 4000,
        closable: true,
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
      toaster.create({ title: 'Check-in registrado', type: 'success', duration: 2500, closable: true });
    },
    onError: () => {
      toaster.create({ title: 'No se pudo registrar el check-in', type: 'error', duration: 3500, closable: true });
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
    <Card.Root key={session.id} variant="outline">
      <Card.Body>
        <VStack gap={3} align="stretch">
          <HStack justify="space-between" align="start">
            <Box>
              <Heading size="sm">{session.gym_class_name}</Heading>
              <Text fontSize="sm">{session.teacher_full_name ?? 'Sin docente asignado'}</Text>
            </Box>
            <Badge colorPalette="gray">{session.available_spots} cupos de referencia</Badge>
          </HStack>
          <Text fontSize="sm">
            {businessTimeLabel(session.starts_at)} - {businessTimeLabel(session.ends_at)}
          </Text>
          <Text fontSize="sm">
            Reservas: {session.current_bookings_count}/{session.capacity_snapshot}
          </Text>
          <Button
            size="sm"
            disabled={isBusy}
            variant={selectedSessionId === session.id ? 'solid' : 'outline'}
            onClick={() => selectSession(session.id)}
          >
            Seleccionar sesión
          </Button>
        </VStack>
      </Card.Body>
    </Card.Root>
  );

  return (
    <Container maxW="80rem" py={8}>
      <VStack gap={8} align="stretch">
        <Box>
          <Heading size="lg">Front Desk</Heading>
          <Text color="gray.600">Identifica primero al cliente y opera reservas y check-in ordinarios.</Text>
        </Box>

        <Box asChild><form
            onSubmit={(event: React.FormEvent) => {
              event.preventDefault();
              if (documentNumber.trim() && !isBusy) {
                setClient(null);
                setSelectedSessionId(null);
                setPreparedBooking(null);
                const intent = nextLookupIntent(lookupIntentRef.current, documentNumber);
                lookupIntentRef.current = intent;
                lookupMutation.mutate(intent);
              }
            }}>
            <VStack align="stretch" gap={3}>
              <Field.Root>
                <Field.Label>Número de documento</Field.Label>
                <Input
                  value={documentNumber}
                  onChange={(event) => {
                    lookupIntentRef.current = nextLookupIntent(lookupIntentRef.current, event.target.value);
                    setDocumentNumber(event.target.value);
                    setClient(null);
                    setSelectedSessionId(null);
                    setPreparedBooking(null);
                  }}
                  placeholder="Documento exacto del cliente"
                />
              </Field.Root>
              <Button type="submit" colorPalette="teal" loading={lookupMutation.isPending}
                disabled={!documentNumber.trim() || isBusy}>
                Buscar cliente
              </Button>
            </VStack>
          </form></Box>

        {client && (
          <Card.Root variant="outline">
            <Card.Body>
              <Text fontWeight="bold">{client.full_name}</Text>
              <Text fontSize="sm">{client.document_number} · {client.email}</Text>
              <Text fontSize="sm" color="gray.600">Cliente identificado; la búsqueda no concede elegibilidad.</Text>
            </Card.Body>
          </Card.Root>
        )}

        {client && (
          <Box>
            <Heading size="md" mb={4}>Sesiones de hoy</Heading>
            {dayQuery.isLoading && <Spinner />}
            {dayQuery.isError && <Text color="red.500">No se pudieron cargar las sesiones.</Text>}
            {dayQuery.data?.sessions.length === 0 && <Text>No hay sesiones programadas para hoy.</Text>}
            {dayQuery.data && dayQuery.data.sessions.length > 0 && (
              <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} gap={4}>
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
              <VStack align="stretch" gap={3}>
                {ownBooking && (
                  <Card.Root variant="outline">
                    <Card.Body>
                      <Text fontWeight="semibold">{ownBooking.client_name}</Text>
                      <Badge mt={2}>{ownBooking.status}</Badge>
                    </Card.Body>
                  </Card.Root>
                )}
                {!ownBooking && (
                  <Button colorPalette="teal" variant="outline"
                    loading={fallbackMutation.isPending}
                    disabled={isBusy}
                    onClick={() => fallbackMutation.mutate({
                      sessionId: selectedSessionId, clientId: client.id,
                    })}>
                    Crear reserva ordinaria
                  </Button>
                )}
                {ownBooking?.status === BookingStatus.CONFIRMED && (
                  <Button colorPalette="teal"
                    loading={checkInMutation.isPending}
                    disabled={isBusy}
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
