import React from 'react';
import {
  Box, Container, Heading, Text, Grid, GridItem, Card, CardBody,
  VStack, HStack, Button, Badge, Icon, Skeleton, Alert, AlertIcon,
} from '@chakra-ui/react';
import { FiCalendar, FiCreditCard } from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../context/useAuth';
import classService from '../services/classService';
import { currentBusinessWeek } from '../utils/businessTimezone';

import WeeklyCalendar from '../components/dashboard/WeeklyCalendar';
import NotificationPanel from '../components/dashboard/NotificationPanel';
import PaymentReminder from '../components/dashboard/PaymentReminder';
import DocumentReminder from '../components/dashboard/DocumentReminder';
import UpcomingEvents from '../components/dashboard/UpcomingEvents';

const HomePage = () => {
  const navigate = useNavigate();
  const { currentUser, isAuthenticated, isClient } = useAuth();
  const weekDays = React.useMemo(() => currentBusinessWeek(), []);
  const weekStart = weekDays[0];

  const agendaQuery = useQuery({
    queryKey: ['clientWeeklyAgenda', weekStart, currentUser?.email],
    queryFn: () => classService.getClientWeeklyAgenda(weekStart),
    enabled: isAuthenticated && isClient,
  });

  const agenda = agendaQuery.data;
  const ownBookingsCount = agenda?.items.filter((item) => item.own_booking !== null).length ?? 0;

  return (
    <Container maxW="container.xl" py={6}>
      <VStack spacing={6} align="stretch">
        <Box>
          <Heading size="lg" mb={2}>Mi Dashboard</Heading>
          <Text color="gray.600">Bienvenido de vuelta, {currentUser?.email ?? 'Cliente'}</Text>
        </Box>
        <Grid templateColumns={{ base: '1fr', lg: '2fr 1fr' }} gap={6}>
          <GridItem>
            <VStack spacing={6} align="stretch">
              <Card>
                <CardBody>
                  <HStack justify="space-between" mb={4}>
                    <Heading size="md" display="flex" alignItems="center">
                      <Icon as={FiCalendar} mr={2} />
                      Agenda semanal
                    </Heading>
                    <Badge colorScheme="blue" fontSize="sm" px={2} py={1}>
                      {ownBookingsCount} {ownBookingsCount === 1 ? 'reserva' : 'reservas'}
                    </Badge>
                  </HStack>
                  {!isAuthenticated || !isClient ? (
                    <Text color="gray.600">La agenda semanal está disponible para clientes autenticados.</Text>
                  ) : agendaQuery.isPending ? (
                    <VStack spacing={3}>
                      <Skeleton height="40px" />
                      <Skeleton height="120px" />
                    </VStack>
                  ) : agendaQuery.isError ? (
                    <Alert status="error"><AlertIcon />No se pudo cargar la agenda semanal. Reintentá desde el panel.</Alert>
                  ) : (
                    <WeeklyCalendar weekDays={weekDays} items={agenda?.items ?? []} />
                  )}
                </CardBody>
              </Card>
              <HStack spacing={4}>
                <Button size="lg" colorScheme="blue" leftIcon={<FiCalendar />} onClick={() => navigate('/classes')} flex={1}>
                  Ver Todas las Clases
                </Button>
                <Button size="lg" variant="outline" leftIcon={<FiCreditCard />} onClick={() => navigate('/payments')} flex={1} isDisabled>
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
