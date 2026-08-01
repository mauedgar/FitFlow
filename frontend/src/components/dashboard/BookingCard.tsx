// src/components/dashboard/BookingCard.tsx
import React from 'react';
import { 
  Box, Text, HStack, VStack, Icon, IconButton, useToast,
  Flex, Stack, useBreakpointValue, Button
} from '@chakra-ui/react';
import { FiClock, FiX, FiUser, FiMapPin } from 'react-icons/fi';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import classService from '../../services/classService';
import { getFormattedDateTime } from '../../utils/formatters';
import type { Booking } from '../../types';

interface BookingCardProps {
  booking: Booking;
  compact?: boolean;
}

const BookingCard: React.FC<BookingCardProps> = ({ booking, compact = false }) => {
  const toast = useToast();
  const queryClient = useQueryClient();
  const isMobile = useBreakpointValue({ base: true, md: false });
  
  // Extraer datos
  const startDateTime = new Date(booking.class_session.starts_at);
  const startTime = `${startDateTime.getHours().toString().padStart(2, '0')}:${startDateTime.getMinutes().toString().padStart(2, '0')}`;
  const duration = booking.class_session.class_schedule?.gym_class?.duration_minutes || 60;
  const className = booking.class_session.class_schedule?.gym_class?.first_name || 'Clase';
  const teacherName = `${booking.class_session.class_schedule?.teacher.first_name} ${booking.class_session.class_schedule?.teacher.last_name}`.trim() || 'Instructor';
  const endDateTime = new Date(startDateTime); 
  endDateTime.setMinutes(startDateTime.getMinutes() + duration);
  const endTime = `${endDateTime.getHours().toString().padStart(2, '0')}:${endDateTime.getMinutes().toString().padStart(2, '0')}`;

  // Mutación para cancelar
  const cancelMutation = useMutation({
    mutationFn: () => classService.cancelBooking(booking.id),
    onSuccess: () => {
      toast({
        title: 'Reserva cancelada',
        status: 'success',
        duration: 3000,
      });
      queryClient.invalidateQueries({ queryKey: ['myBookings'] });
    },
    onError: () => {
      toast({
        title: 'Error al cancelar',
        description: 'No se pudo cancelar la reserva',
        status: 'error',
        duration: 3000,
      });
    }
  });

  // Versión compacta para calendario
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
            toast({
              title: className,
              description: `${startTime} - ${endTime} hs con ${teacherName}`,
              status: 'info',
              duration: 4000,
              isClosable: true,
            });
          }
        }}
      >
        <Text 
          fontWeight="bold" 
          color="blue.700" 
          mb={1} 
          noOfLines={1}
          fontSize={{ base: "xs", md: "sm" }}
        >
          {className}
        </Text>
        <HStack justify="space-between">
          <Text color="gray.600">{startTime} - {endTime} hs</Text>          
          <Text color="gray.600"> {teacherName}</Text>
        </HStack>
      </Box>
    );
  }

  // Versión completa
  return (
    <Box
      p={{ base: 3, md: 4 }}
      borderWidth="1px"
      borderRadius="md"
      bg="white"
      shadow="sm"
      _hover={{ shadow: 'md' }}
      transition="all 0.2s"
    >
      <Stack
        direction={{ base: 'column', md: 'row' }}
        justify="space-between"
        align={{ base: 'stretch', md: 'start' }}
        spacing={{ base: 3, md: 4 }}
      >
        <VStack align="start" spacing={2} flex={1}>
          <Text 
            fontSize={{ base: "md", md: "lg" }} 
            fontWeight="bold"
            noOfLines={2}
          >
            {className}
          </Text>
          
          <VStack align="start" spacing={1} w="100%">
            <HStack fontSize={{ base: "sm", md: "md" }} color="gray.600">
              <Icon as={FiUser} boxSize={{ base: 3, md: 4 }} />
              <Text noOfLines={1}>{teacherName}</Text>
            </HStack>
            
            <HStack fontSize={{ base: "sm", md: "md" }} color="gray.600">
              <Icon as={FiClock} boxSize={{ base: 3, md: 4 }} />
              <Text>{getFormattedDateTime(booking.class_session.starts_at)}</Text>
            </HStack>
            
            <HStack fontSize={{ base: "sm", md: "md" }} color="gray.600">
              <Icon as={FiMapPin} boxSize={{ base: 3, md: 4 }} />
              <Text>Sala principal</Text>
            </HStack>
          </VStack>
        </VStack>

        <Flex 
          direction={{ base: 'row', md: 'column' }}
          justify={{ base: 'flex-end', md: 'start' }}
          align={{ base: 'center', md: 'end' }}
          gap={2}
        >
          {isMobile ? (
            <Button
              size="sm"
              colorScheme="red"
              variant="outline"
              leftIcon={<FiX />}
              onClick={() => cancelMutation.mutate()}
              isLoading={cancelMutation.isPending}
              minW="100px"
            >
              Cancelar
            </Button>
          ) : (
            <IconButton
              aria-label="Cancelar reserva"
              icon={<FiX />}
              size="sm"
              colorScheme="red"
              variant="ghost"
              onClick={() => cancelMutation.mutate()}
              isLoading={cancelMutation.isPending}
            />
          )}
        </Flex>
      </Stack>
    </Box>
  );
};

export default BookingCard;