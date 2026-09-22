import React from 'react';
import {
  Box,
  Grid,
  GridItem,
  Heading,
  Text,
  VStack,
} from '@chakra-ui/react';
import type { Booking } from '../../types';
import BookingCard from './BookingCard';

interface WeeklyCalendarProps {
  weekDays: Date[];
  bookings: Booking[];
}

const isSameLocalDay = (left: Date, right: Date) =>
  left.getFullYear() === right.getFullYear() &&
  left.getMonth() === right.getMonth() &&
  left.getDate() === right.getDate();

const WeeklyCalendar: React.FC<WeeklyCalendarProps> = ({ weekDays, bookings }) => {
  return (
    <Grid
      templateColumns={{ base: '1fr', md: 'repeat(5, minmax(0, 1fr))' }}
      gap={3}
    >
      {weekDays.map((day) => {
        const dayBookings = bookings.filter((booking) =>
          isSameLocalDay(new Date(booking.starts_at), day),
        );

        return (
          <GridItem key={day.toISOString()}>
            <Box borderWidth="1px" borderRadius="md" p={3} minH="150px">
              <Heading size="xs" mb={3}>
                {day.toLocaleDateString([], {
                  weekday: 'short',
                  day: '2-digit',
                  month: '2-digit',
                })}
              </Heading>

              {dayBookings.length === 0 ? (
                <Text fontSize="sm" color="gray.500">
                  Sin clases
                </Text>
              ) : (
                <VStack spacing={2} align="stretch">
                  {dayBookings.map((booking) => (
                    <BookingCard key={booking.id} booking={booking} compact />
                  ))}
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