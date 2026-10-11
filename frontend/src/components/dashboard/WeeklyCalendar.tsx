import React from 'react';
import {
  Badge, Box, Button, Grid, GridItem, Heading, HStack, Text,
  VStack, useToast,
} from '@chakra-ui/react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { BookingStatus, type ClientWeeklyAgendaItem } from '../../types';
import classService from '../../services/classService';
import { businessDateKey, businessDayLabel, businessTimeLabel } from '../../utils/businessTimezone';

interface WeeklyCalendarProps {
  weekDays: string[];
  items: ClientWeeklyAgendaItem[];
}

const WeeklyCalendar: React.FC<WeeklyCalendarProps> = ({ weekDays, items }) => {
  const toast = useToast();
  const queryClient = useQueryClient();
  const refreshAgenda = () => {
    void queryClient.invalidateQueries({ queryKey: ['clientWeeklyAgenda'] });
    void queryClient.invalidateQueries({ queryKey: ['myBookings'] });
  };

  // Booking and cancellation are separate ordinary backend commands.
  const reserveMutation = useMutation({
    mutationFn: (sessionId: string) => classService.createBooking({
      class_session_id: sessionId,
      status: BookingStatus.CONFIRMED,
    }),
    onSuccess: () => {
      toast({ title: 'Reserva confirmada', status: 'success', duration: 3000 });
      refreshAgenda();
    },
    onError: () => {
      toast({ title: 'No se pudo crear la reserva', status: 'error', duration: 4000 });
      refreshAgenda();
    },
  });
  const cancelMutation = useMutation({
    mutationFn: (bookingId: string) => classService.cancelBooking(bookingId),
    onSuccess: () => {
      toast({ title: 'Reserva cancelada', status: 'success', duration: 3000 });
      refreshAgenda();
    },
    onError: () => {
      toast({ title: 'No se pudo cancelar la reserva', status: 'error', duration: 4000 });
      refreshAgenda();
    },
  });

  const isMutating = reserveMutation.isPending || cancelMutation.isPending;

  return (
    <Grid templateColumns={{ base: '1fr', md: 'repeat(7, minmax(0, 1fr))' }} gap={2}>
      {weekDays.map((day) => {
        const dayItems = items.filter((item) => businessDateKey(new Date(item.starts_at)) === day);
        return (
          <GridItem key={day} minW={0}>
            <Box borderWidth="1px" borderRadius="md" p={2} minH="150px">
              <Heading size="xs" mb={3}>
                {businessDayLabel(day)}
              </Heading>
              {dayItems.length === 0 ? (
                <Text fontSize="xs" color="gray.500">Sin ofertas elegibles</Text>
              ) : (
                <VStack spacing={2} align="stretch">
                  {dayItems.map((item) => {
                    const ownBooking = item.own_booking;
                    const hasBooking = ownBooking !== null;
                    const canCancel = ownBooking?.status === BookingStatus.CONFIRMED;
                    const canReserve = !hasBooking && item.membership_plan_eligible &&
                      (item.status === 'scheduled' || item.status === 'open') &&
                      new Date(item.starts_at) > new Date();
                    const capacityReached = item.reference_capacity !== null &&
                      item.active_booking_count >= item.reference_capacity;
                    return (
                      <Box key={item.session_id} borderWidth="1px" borderRadius="md" p={2} bg={hasBooking ? 'blue.50' : 'gray.50'}>
                        <Text fontSize="xs" fontWeight="bold">{item.activity_name}</Text>
                        <Text fontSize="xs">{businessTimeLabel(item.starts_at)} – {businessTimeLabel(item.ends_at)}</Text>
                        <Text fontSize="xs" color="gray.600">
                          Demanda: {item.active_booking_count}
                          {item.reference_capacity !== null ? ` / ref. ${item.reference_capacity}` : ''}
                        </Text>
                        {capacityReached && (
                          <Text fontSize="xs" color="purple.600">Referencia alcanzada (no bloquea)</Text>
                        )}
                        <HStack mt={2} wrap="wrap" spacing={1}>
                          {hasBooking ? (
                            <>
                              <Badge colorScheme="blue">{ownBooking.status}</Badge>
                              {canCancel && (
                                <Button size="xs" colorScheme="red" variant="outline"
                                  isLoading={cancelMutation.isPending}
                                  isDisabled={isMutating}
                                  onClick={() => cancelMutation.mutate(ownBooking.booking_id)}>
                                  Cancelar
                                </Button>
                              )}
                            </>
                          ) : (
                            <Button size="xs" colorScheme="teal" isLoading={reserveMutation.isPending}
                              isDisabled={isMutating || !canReserve}
                              onClick={() => reserveMutation.mutate(item.session_id)}>
                              Reservar
                            </Button>
                          )}
                        </HStack>
                      </Box>
                    );
                  })}
                </VStack>
              )}
            </Box>
          </GridItem>
        );
      })}
    </Grid>
  );
};

export default WeeklyCalendar;
