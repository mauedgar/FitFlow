// src/components/dashboard/NotificationPanel.tsx
import React from 'react';
import { 
  Card, CardBody, VStack, Text, Progress, 
  Skeleton, Alert, AlertIcon 
} from '@chakra-ui/react';
import { useAuth } from '../../context/useAuth';
import { BookingStatus } from '../../types';

const NotificationPanel: React.FC = () => {
  const { userBookings = [], isLoadingBookings } = useAuth();
  
  // 🚀 Usar los datos que ya están en cache del AuthContext
  // No hacer queries adicionales innecesarias
  
  const monthlyStats = React.useMemo(() => {
    if (!userBookings) return { current: 0, limit: 10, percentage: 0 };
    
    const currentMonth = new Date().getMonth();
    const currentYear = new Date().getFullYear();
    
    const classesThisMonth = userBookings.filter(booking => {
      const bookingDate = new Date(booking.class_session.start_datetime);
      return (
        bookingDate.getMonth() === currentMonth &&
        bookingDate.getFullYear() === currentYear &&
        booking.status === BookingStatus.CONFIRMED
      );
    }).length;

    const monthlyLimit = 10; // Esto vendría de tu API de perfil/plan
    const percentage = Math.min((classesThisMonth / monthlyLimit) * 100, 100);
    
    return {
      current: classesThisMonth,
      limit: monthlyLimit,
      percentage
    };
  }, [userBookings]);

  if (isLoadingBookings) {
    return (
      <Card size="sm">
        <CardBody>
          <VStack spacing={3} align="stretch">
            <Skeleton height="16px" />
            <Skeleton height="8px" />
            <Skeleton height="12px" />
          </VStack>
        </CardBody>
      </Card>
    );
  }

  const { current, limit, percentage } = monthlyStats;
  const isNearLimit = percentage > 80;
  const colorScheme = isNearLimit ? "orange" : percentage > 60 ? "yellow" : "green";

  return (
    <Card size="sm">
      <CardBody>
        <VStack spacing={3} align="stretch">
          <Text fontWeight="bold" fontSize="sm">Estado de Cuenta</Text>
          
          <Progress 
            value={percentage} 
            colorScheme={colorScheme} 
            size="sm" 
            borderRadius="full"
            bg="gray.100"
          />
          
          <Text fontSize="xs" color="gray.600">
            {current} de {limit} clases utilizadas este mes
          </Text>
          
          {isNearLimit && (
            <Alert status="warning" size="sm" borderRadius="md">
              <AlertIcon boxSize={3} />
              <Text fontSize="xs">
                Te quedan {limit - current} clases este mes
              </Text>
            </Alert>
          )}
        </VStack>
      </CardBody>
    </Card>
  );
};

export default NotificationPanel;