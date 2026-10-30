import { toaster } from '../ui/toaster-store';
// src/components/dashboard/BookingCard.tsx
import React from 'react';
import {
  Box, Text, HStack, VStack, Icon, IconButton,
  Flex, Stack, useBreakpointValue, Button
} from '@chakra-ui/react';
import { FiClock, FiX, FiMapPin } from 'react-icons/fi';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import classService from '../../services/classService';
import { getFormattedDateTime } from '../../utils/formatters';
import type { Booking } from '../../types';

interface BookingCardProps {
  booking: Booking;
  compact?: boolean;
}

const BookingCard: React.FC<BookingCardProps> = ({ booking, compact = false }) => {
  const queryClient = useQueryClient();
  const isMobile = useBreakpointValue({ base: true, md: false });

  const startDateTime = new Date(booking.starts_at);
  const endDateTime = new Date(booking.ends_at);
  const startTime = `${startDateTime.getHours().toString().padStart(2, '0')}:${startDateTime.getMinutes().toString().padStart(2, '0')}`;
  const endTime = `${endDateTime.getHours().toString().padStart(2, '0')}:${endDateTime.getMinutes().toString().padStart(2, '0')}`;
  const className = booking.gym_class_name;

  const cancelMutation = useMutation({
    mutationFn: () => classService.cancelBooking(booking.id),
    onSuccess: () => {
      toaster.create({
        title: 'Reserva cancelada',
        type: 'success',
        duration: 3000,
      });
      queryClient.invalidateQueries({ queryKey: ['myBookings'] });
    },
    onError: () => {
      toaster.create({
        title: 'Error al cancelar',
        description: 'No se pudo cancelar la reserva',
        type: 'error',
        duration: 3000,
      });
    }
  });

  if (compact) {
    return (
      <Box
        bg="blue.50"
        border="1px"
        borderColor="blue.200"
        borderRadius="md"
        p={{ base: 2, md: 3 }}
        fontSize={{ base: "xs", md: "sm" }}
        position="relative"
        _hover={{ bg: 'blue.100', cursor: 'pointer' }}
        transition="all 0.2s"
        onClick={() => {
          if (isMobile) {
            toaster.create({
              title: className,
              description: `${startTime} - ${endTime} hs`,
              type: 'info',
              duration: 4000,
              closable: true,
            });
          }
        }}
      >
        <Text fontWeight="bold" color="blue.700" mb={1} lineClamp={1} fontSize={{ base: "xs", md: "sm" }}>
          {className}
        </Text>
        <HStack justify="space-between">
          <Text color="gray.600">{startTime} - {endTime} hs</Text>
        </HStack>
      </Box>
    );
  }

  return (
    <Box p={{ base: 3, md: 4 }} borderWidth="1px" borderRadius="md" bg="white" shadow="sm" _hover={{ shadow: 'md' }} transition="all 0.2s">
      <Stack direction={{ base: 'column', md: 'row' }} justify="space-between" align={{ base: 'stretch', md: 'start' }} gap={{ base: 3, md: 4 }}>
        <VStack align="start" gap={2} flex={1}>
          <Text fontSize={{ base: "md", md: "lg" }} fontWeight="bold" lineClamp={2}>
            {className}
          </Text>
          <VStack align="start" gap={1} w="100%">
            <HStack fontSize={{ base: "sm", md: "md" }} color="gray.600">
              <Icon boxSize={{ base: 3, md: 4 }} asChild><FiClock /></Icon>
              <Text>{getFormattedDateTime(booking.starts_at)} - {endTime} hs</Text>
            </HStack>
            <HStack fontSize={{ base: "sm", md: "md" }} color="gray.600">
              <Icon boxSize={{ base: 3, md: 4 }} asChild><FiMapPin /></Icon>
              <Text>Sala principal</Text>
            </HStack>
          </VStack>
        </VStack>

        <Flex direction={{ base: 'row', md: 'column' }} justify={{ base: 'flex-end', md: 'start' }} align={{ base: 'center', md: 'end' }} gap={2}>
          {isMobile ? (
            <Button
              size="sm"
              colorPalette="red"
              variant="outline"
              onClick={() => cancelMutation.mutate()}
              loading={cancelMutation.isPending}
              minW="100px"><FiX />Cancelar
                          </Button>
          ) : (
            <IconButton
              aria-label="Cancelar reserva"
              size="sm"
              colorPalette="red"
              variant="ghost"
              onClick={() => cancelMutation.mutate()}
              loading={cancelMutation.isPending}><FiX /></IconButton>
          )}
        </Flex>
      </Stack>
    </Box>
  );
};

export default BookingCard;