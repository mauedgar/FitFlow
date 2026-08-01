// src/pages/HomePage.tsx (VERSION SIMPLIFICADA)
import React from 'react';
import {
  Box, Container, Heading, Text, Grid, GridItem, Card, CardBody,
  VStack, HStack, Button, Badge, Icon, Skeleton
} from '@chakra-ui/react';
import { FiCalendar, FiCreditCard } from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/useAuth';
import { BookingStatus, type Booking } from '../types';

// Componentes del dashboard
import WeeklyCalendar from '../components/dashboard/WeeklyCalendar';
import NotificationPanel from '../components/dashboard/NotificationPanel';
import PaymentReminder from '../components/dashboard/PaymentReminder';
import DocumentReminder from '../components/dashboard/DocumentReminder';
import UpcomingEvents from '../components/dashboard/UpcomingEvents';

const HomePage = () => {
  const navigate = useNavigate();
  const { 
    currentUser, 
    userBookings = [], 
    isLoadingBookings
  } = useAuth();

  const weekDays = React.useMemo(() => {
    const today = new Date(); 
    // const debugToday = new Date('2025-09-12T10:00:00-03:00'); // <--- DESCOMENTA Y USA ESTO PARA PROBAR CON 2025
    // const today = debugToday; // <--- Y USA ESTA LINEA EN LUGAR DE LA DE ARRIBA PARA 'today'

    console.log("Fecha 'today' usada para weekDays:", today.toISOString()); // <-- ¡MANTEN ESTE LOG!

    const startOfWeek = new Date(today);
    // Ajusta para llegar al lunes de la semana actual. (Maneja el caso de domingo como 0)
    startOfWeek.setDate(today.getDate() - today.getDay() + (today.getDay() === 0 ? -6 : 1)); 
    startOfWeek.setHours(0, 0, 0, 0); // <-- CLAVE: Asegura que el Lunes inicial esté en 00:00:00 local

    return Array.from({ length: 5 }, (_, i) => {
      const day = new Date(startOfWeek); // Crea una copia a partir del Lunes 00:00:00 local
      day.setDate(startOfWeek.getDate() + i); // Añade los días restantes
      // No necesitas day.setHours(0,0,0,0) aquí, ya que startOfWeek ya está en 00:00:00
      return day;
    });
  }, [/* Si usas debugToday, ponlo aquí. Si usas new Date(), déjalo vacío. */]);
  const thisWeekBookings = React.useMemo(() => {
    console.log('--- Starting thisWeekBookings calculation (Timezone Corrected) ---');
    console.log('Total userBookings:', userBookings.length);
    console.log("Fecha 'today' usada para weekDays (confirmación):", (new Date()).toISOString()); // Mantén este para verificar que no cambie

    if (!weekDays || weekDays.length === 0) {
      console.log('weekDays is not ready.');
      return [];
    }

    // Asegúrate de que weekDays[0] y weekDays[4] ya estén en 00:00:00 local
    // (Esto debería estar resuelto por el `setHours(0,0,0,0)` en la generación de weekDays)
    
    const weekStartLocal = weekDays[0]; 
    const weekEndLocalCandidate = weekDays[4];
    const weekEndLocal = new Date(weekEndLocalCandidate); 
    weekEndLocal.setHours(23, 59, 59, 999); 

    const weekStartTimeMs = weekStartLocal.getTime(); 
    const weekEndTimeMs = weekEndLocal.getTime();

    console.log(`  Calculated local week range:`);
    console.log(`    Start (local): ${weekStartLocal.toLocaleString()} (ms: ${weekStartTimeMs})`);
    console.log(`    End (local):   ${weekEndLocal.toLocaleString()} (ms: ${weekEndTimeMs})`);


    const filteredBookings = userBookings.filter((booking: Booking) => {    

      if (booking.status !== BookingStatus.CONFIRMED) {
        return false;
      }
      
      const bookingDate = new Date(booking.class_session.starts_at);
      const bookingTimeMs = bookingDate.getTime();

      const isInRange = bookingTimeMs >= weekStartTimeMs && bookingTimeMs <= weekEndTimeMs;      

      return isInRange;
    });
    return filteredBookings;
  }, [userBookings, weekDays]); // Dependencias correctas

  return (
    <Container maxW="container.xl" py={6}>
      <VStack spacing={6} align="stretch">
        <Box>
          <Heading size="lg" mb={2}>Mi Dashboard</Heading>
          <Text color="gray.600">
            Bienvenido de vuelta, {currentUser?.id|| 'Cliente'}
          </Text>
        </Box>

        <Grid templateColumns={{ base: '1fr', lg: '2fr 1fr' }} gap={6}>
          <GridItem>
            <VStack spacing={6} align="stretch">
              <Card>
                <CardBody>
                  <HStack justify="space-between" mb={4}>
                    <Heading size="md" display="flex" alignItems="center">
                      <Icon as={FiCalendar} mr={2} />
                      Mis Clases de la Semana
                    </Heading>
                    <Badge colorScheme="blue" fontSize="sm" px={2} py={1}>
                      {thisWeekBookings.length} {thisWeekBookings.length === 1 ? 'clase' : 'clases'}
                    </Badge>
                  </HStack>

                  {isLoadingBookings ? (
                    <VStack spacing={3}>
                      <Skeleton height="40px" />
                      <Skeleton height="120px" />
                    </VStack>
                  ) : (
                    <WeeklyCalendar 
                      weekDays={weekDays} 
                      bookings={thisWeekBookings}
                    />
                  )}
                </CardBody>
              </Card>

              <HStack spacing={4}>
                <Button 
                  size="lg" 
                  colorScheme="blue" 
                  leftIcon={<FiCalendar />}
                  onClick={() => navigate('/classes')}
                  flex={1}
                >
                  Ver Todas las Clases
                </Button>
                <Button 
                  size="lg" 
                  variant="outline" 
                  leftIcon={<FiCreditCard />}
                  onClick={() => navigate('/payments')}
                  flex={1}
                  isDisabled
                >
                  Ver Pagos
                </Button>
              </HStack>
            </VStack>
          </GridItem>

          <GridItem>
            <VStack spacing={4} align="stretch">
              <Heading size="md">Notificaciones</Heading>
              <NotificationPanel />
              <PaymentReminder />
              <DocumentReminder />
              <UpcomingEvents />
            </VStack>
          </GridItem>
        </Grid>
      </VStack>
    </Container>
  );
};

export default HomePage;