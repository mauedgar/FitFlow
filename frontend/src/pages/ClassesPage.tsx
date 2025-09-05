import React, { useState } from 'react';
import { Container, Heading, Box } from '@chakra-ui/react';
import { useQuery } from '@tanstack/react-query'; // 1. Importamos useQuery
import classService from '../services/classService';
import ClassList from '../components/classes/ClassList';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorDisplay from '../components/common/ErrorDisplay';
import ClassDetailModal from '../components/classes/ClassDetailModal';// El nuevo modal

const ClassesPage: React.FC = () => {
  const [selectedClassId, setSelectedClassId] = useState<string | null>(null);

  // 2. Reemplazamos todos los useState y el useEffect con esta única línea
  const { 
    data: classes, // Renombramos 'data' a 'classes' para mayor claridad
    isLoading, 
    isError, 
    error 
  } = useQuery({
    queryKey: ['classes'], // Una clave única para identificar esta petición
    queryFn: classService.getAllClasses, // La función que devuelve la promesa
  });
  // Funciones para abrir y cerrar el modal, que se pasarán como props
  const handleClassSelect = (classId: string) => setSelectedClassId(classId);
  const handleCloseModal = () => setSelectedClassId(null);
  // 3. Tu lógica de renderizado ahora es aún más limpia
  const renderContent = () => {
    if (isLoading) return <LoadingSpinner />;
    // isError es un booleano que nos dice si 'error' tiene un valor
    if (isError) {
      const errorMessage = error instanceof Error ? error.message : 'Ocurrió un error inesperado';
      return <ErrorDisplay message={errorMessage} />;
    }
    if (!classes || classes.length === 0) {
      return <Heading as="h3" size="md">No hay clases disponibles.</Heading>;
    }    
    // Pasamos la función para manejar la selección a la lista
    return <ClassList classes={classes} onClassSelect={handleClassSelect}/>;
  };

  return (
    <Container maxW="container.xl" py={10}>
      <Heading as="h1" size="2xl" mb={8} textAlign="center" color="gray.700">
        Nuestro Catálogo de Clases
      </Heading>
      <Box>
        {renderContent()}
      </Box>
      {/* El Modal se renderiza aquí, pero solo se mostrará si tiene un classId.
        Su estado `isOpen` y su `classId` son controlados por esta página. */}
      <ClassDetailModal
        classId={selectedClassId}
        isOpen={selectedClassId !== null}
        onClose={handleCloseModal}
      />
    </Container>
  );
};

export default ClassesPage;