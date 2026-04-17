// src/components/dashboard/UpcomingEvents.tsx
import React from 'react';
import { 
  Card, CardBody, VStack, Text, Divider, HStack, Icon, Box,
  Skeleton, Alert, AlertIcon
} from '@chakra-ui/react';
import { FiClock, FiCalendar, FiTrendingUp } from 'react-icons/fi';

// Tipo para eventos (esto vendría de tu API más adelante)
interface Event {
  id: number;
  name: string;
  date: string;
  time: string;
  type: 'tournament' | 'workshop' | 'special';
}

const UpcomingEvents: React.FC = () => {
  // 🚀 TanStack Query para eventos futuros (por ahora mock data)
  // const { data: events = [], isLoading } = useQuery({
  //   queryKey: ['upcomingEvents'],
  //   queryFn: () => classService.getUpcomingEvents(),
  //   staleTime: 10 * 60 * 1000, // 10 minutos
  // });

  // Mock data por ahora
  const isLoading = false;
  const events: Event[] = [
    { 
      id: 1, 
      name: 'Torneo CrossFit', 
      date: '15 Oct', 
      time: '18:00',
      type: 'tournament'
    },
    { 
      id: 2, 
      name: 'Workshop Nutrición', 
      date: '20 Oct', 
      time: '10:00',
      type: 'workshop'
    },
    { 
      id: 3, 
      name: 'Clase Especial Yoga', 
      date: '25 Oct', 
      time: '19:00',
      type: 'special'
    }
  ];

  const getEventIcon = (type: Event['type']) => {
    switch (type) {
      case 'tournament': return FiTrendingUp;
      case 'workshop': return FiCalendar;
      default: return FiClock;
    }
  };

  const getEventColor = (type: Event['type']) => {
    switch (type) {
      case 'tournament': return 'orange.500';
      case 'workshop': return 'green.500';
      default: return 'blue.500';
    }
  };

  if (isLoading) {
    return (
      <Card size="sm">
        <CardBody>
          <VStack spacing={2} align="stretch">
            <Skeleton height="20px" />
            <Skeleton height="40px" />
            <Skeleton height="40px" />
          </VStack>
        </CardBody>
      </Card>
    );
  }

  if (events.length === 0) {
    return (
      <Alert status="info" borderRadius="md">
        <AlertIcon />
        <Text fontSize="sm">No hay eventos próximos</Text>
      </Alert>
    );
  }

  return (
    <Card size="sm">
      <CardBody>
        <VStack spacing={3} align="stretch">
          <Text fontWeight="bold" fontSize="sm">Próximos Eventos</Text>
          <Divider />
          
          <VStack spacing={3} align="stretch">
            {events.slice(0, 3).map(event => ( // Solo mostrar 3 eventos
              <HStack key={event.id} spacing={3}>
                <Icon 
                  as={getEventIcon(event.type)} 
                  color={getEventColor(event.type)}
                  boxSize={4}
                />
                <Box flex={1} fontSize="xs">
                  <Text fontWeight="medium" noOfLines={1}>
                    {event.name}
                  </Text>
                  <Text color="gray.500">
                    {event.date} - {event.time}
                  </Text>
                </Box>
              </HStack>
            ))}
          </VStack>
        </VStack>
      </CardBody>
    </Card>
  );
};

export default UpcomingEvents;