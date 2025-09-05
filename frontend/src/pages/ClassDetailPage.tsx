// Crea este nuevo archivo: src/pages/ClassDetailPage.tsx

import React from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Container, Box } from '@chakra-ui/react';
import classService from '../services/classService';
import ClassDetailView from '../components/classes/ClassDetailView'; // Importamos la "carrocería"
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorDisplay from '../components/common/ErrorDisplay';
import { AxiosError } from 'axios';

// Este es el componente CONTENEDOR ("inteligente")
const ClassDetailPage: React.FC = () => {
  // 1. Obtiene el ID de la URL (el "conductor" sabe a dónde ir)
  const { classId } = useParams<{ classId: string }>();

  // 2. Usa TanStack Query para obtener los datos (el "motor")
  const { data: gymClass, isLoading, isError, error } = useQuery({
    queryKey: ['class', classId],
    queryFn: () => {
      if (!classId) throw new Error("No class ID provided");
      return classService.getClassById(classId);
    },
    enabled: !!classId,
    retry: (failureCount, err) => {
        if (err instanceof AxiosError && err.response?.status === 404) {
            return false;
        }
        return failureCount < 3;
    }
  });

  // 3. Decide qué mostrar basado en el estado de la petición
  const renderContent = () => {
    if (isLoading) return <LoadingSpinner />;

    if (isError) {
      if (error instanceof AxiosError && error.response?.status === 404) {
        return <ErrorDisplay message={`La clase con ID ${classId} no fue encontrada.`} />;
      }
      return <ErrorDisplay message={error.message || 'Ocurrió un error al cargar los detalles.'} />;
    }
    
    // 4. Si hay datos, le pasa la información a la "carrocería" (ClassDetailView)
    return gymClass ? <ClassDetailView gymClass={gymClass} /> : null;
  };

  return (
    <Container maxW="container.lg" py={10}>
      <Box>
        {renderContent()}
      </Box>
    </Container>
  );
};

export default ClassDetailPage;