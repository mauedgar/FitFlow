// src/components/dashboard/WeeklyCalendar.tsx
import React from 'react';
import {
  Table, Thead, Tbody, Tr, Th, Td,
  VStack, Text, Box, useBreakpointValue,
  Heading
} from '@chakra-ui/react';
import BookingCard from './BookingCard';
import { getFormattedDate } from '../../utils/formatters';
import type { Booking } from '../../types'; // ✅ Tipo específico, no any

interface WeeklyCalendarProps {
  weekDays: Date[];
  bookings: Booking[]; // ✅ Tipo específico
}

const WeeklyCalendar: React.FC<WeeklyCalendarProps> = ({ weekDays, bookings }) => {
  const isMobile = useBreakpointValue({ base: true, md: false });
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const getBookingsForDay = (day: Date): Booking[] => {
    const dayStr = getFormattedDate(day);
    return bookings.filter(booking => {
      const bookingDate = getFormattedDate(booking.class_session.start_datetime);
      return bookingDate === dayStr;
    }).sort((a, b) => 
      new Date(a.class_session.start_datetime).getTime() - 
      new Date(b.class_session.start_datetime).getTime()
    );
  };

  const getDayName = (date: Date): string => {
    const days = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
    return days[date.getDay()];
  };

  const isToday = (date: Date): boolean => {
    const dateStr = getFormattedDate(date);
    const todayStr = getFormattedDate(today);
    return dateStr === todayStr;
  };

  // Vista móvil: lista vertical
  if (isMobile) {
    return (
      <VStack spacing={4} align="stretch">
        {weekDays.map(day => {
          const dayBookings = getBookingsForDay(day);
          const dayName = getDayName(day);
          const isTodayFlag = isToday(day);
          
          return (
            <Box key={day.toISOString()}>
              <Heading 
                size="sm" 
                mb={2}
                color={isTodayFlag ? 'blue.500' : 'gray.700'}
              >
                {dayName} {day.getDate()}
                {isTodayFlag && <Text as="span" ml={2} fontSize="xs">(Hoy)</Text>}
              </Heading>
              
              {dayBookings.length === 0 ? (
                <Text fontSize="sm" color="gray.400" ml={4}>
                  Sin clases
                </Text>
              ) : (
                <VStack spacing={2} align="stretch" pl={2}>
                  {dayBookings.map(booking => (
                    <BookingCard 
                      key={booking.id} 
                      booking={booking} 
                      compact={true}
                    />
                  ))}
                </VStack>
              )}
            </Box>
          );
        })}
      </VStack>
    );
  }

  // Vista desktop: tabla
  return (
    <Table variant="simple" size="sm">
      <Thead>
        <Tr>
          {weekDays.map(day => (
            <Th key={day.toISOString()} textAlign="center" p={2}>
              <VStack spacing={1}>
                <Text fontSize="xs" color="gray.500">
                  {getDayName(day)}
                </Text>
                <Text 
                  fontSize="lg" 
                  fontWeight="bold"
                  color={isToday(day) ? 'blue.500' : 'gray.700'}
                >
                  {day.getDate()}
                </Text>
              </VStack>
            </Th>
          ))}
        </Tr>
      </Thead>
      <Tbody>
        <Tr>
          {weekDays.map(day => {
            const dayBookings = getBookingsForDay(day);
            return (
              <Td key={day.toISOString()} p={2} verticalAlign="top">
                <VStack spacing={2} align="stretch" minH="120px">
                  {dayBookings.length === 0 ? (
                    <Text fontSize="xs" color="gray.400" textAlign="center">
                      Sin clases
                    </Text>
                  ) : (
                    dayBookings.map(booking => (
                      <BookingCard 
                        key={booking.id} 
                        booking={booking} 
                        compact={true}
                      />
                    ))
                  )}
                </VStack>
              </Td>
            );
          })}
        </Tr>
      </Tbody>
    </Table>
  );
};

export default WeeklyCalendar;