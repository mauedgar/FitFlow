import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Alert, Badge, Box, Button, Center, Heading, HStack, Input,
  SimpleGrid, Skeleton, Stack, Table, Text, VStack,
} from '@chakra-ui/react';
import { LuRefreshCw, LuSearch } from 'react-icons/lu';
import { useAuth } from '../../context/useAuth';
import { getAdminGymClassSummaries, type AdminGymClassSummary } from '../../services/adminReadService';

const matches = (gymClass: AdminGymClassSummary, term: string) =>
  [gymClass.name, gymClass.description]
    .some((field) => field.toLocaleLowerCase().includes(term));

const CrudClassesPage = () => {
  const { currentUser } = useAuth();
  const [search, setSearch] = useState('');
  const { data = [], isLoading, isError, isFetching, refetch } = useQuery({
    queryKey: ['adminGymClassSummaries', currentUser?.email],
    queryFn: ({ signal }) => getAdminGymClassSummaries(signal),
    enabled: currentUser?.role === 'admin',
    retry: 1,
  });
  const term = search.trim().toLocaleLowerCase();
  const visible = useMemo(() => data.filter((item) => matches(item, term)), [data, term]);

  return (
    <Box maxW="1200px" mx="auto">
      <Stack direction={{ base: 'column', md: 'row' }} justify="space-between"
        align={{ base: 'stretch', md: 'center' }} gap={4} mb={6}>
        <Box>
          <Heading as="h1" size="lg">Clases</Heading>
          <Text color="gray.600" mt={1}>Catálogo de actividades disponible para consulta.</Text>
        </Box>
        <Badge colorPalette="teal" alignSelf={{ base: 'start', md: 'center' }}>
          {isError ? 'No disponible' : isLoading ? 'Cargando…' : `${data.length} clases recibidas`}
        </Badge>
      </Stack>
      <Stack direction={{ base: 'column', sm: 'row' }} gap={3} mb={5}>
        <Box flex="1" position="relative">
          <Box color="gray.500" position="absolute" left={3} top="50%"
            transform="translateY(-50%)" pointerEvents="none"><LuSearch aria-hidden="true" /></Box>
          <Input aria-label="Buscar clases de los registros recibidos" pl={10}
            placeholder="Buscar por actividad" value={search}
            onChange={(event) => setSearch(event.target.value)}
            disabled={isLoading || isError} />
        </Box>
        <Button colorPalette="teal" variant="outline" loading={isFetching}
          onClick={() => void refetch()}><LuRefreshCw aria-hidden="true" />Actualizar</Button>
      </Stack>
      {isError ? (
        <Alert.Root status="error" borderRadius="lg" role="alert">
          <Alert.Indicator /><Alert.Content>
            <Alert.Title>No pudimos cargar el catálogo.</Alert.Title>
            <Alert.Description>Comprobá la conexión y volvé a intentar.</Alert.Description>
          </Alert.Content>
        </Alert.Root>
      ) : isLoading ? (
        <Stack role="status" aria-label="Cargando clases" gap={3}>
          <Skeleton height="56px" /><Skeleton height="56px" /><Text>Consultando clases…</Text>
        </Stack>
      ) : visible.length === 0 ? (
        <Center bg="white" borderWidth="1px" borderRadius="xl" p={10}>
          <VStack gap={3} textAlign="center">
            <Heading as="h2" size="md">
              {data.length === 0 ? 'Todavía no hay clases disponibles' : 'No encontramos coincidencias'}
            </Heading>
            <Text color="gray.600">
              {data.length === 0 ? 'Las clases aparecerán aquí cuando existan en el catálogo.' : 'Probá con otra actividad.'}
            </Text>
            {term && <Button variant="plain" colorPalette="teal" onClick={() => setSearch('')}>Limpiar búsqueda</Button>}
          </VStack>
        </Center>
      ) : (
        <>
          <Box display={{ base: 'none', md: 'block' }} bg="white" borderRadius="xl"
            borderWidth="1px" overflowX="auto">
            <Table.Root variant="line">
              <Table.Header><Table.Row>
                <Table.ColumnHeader>Actividad</Table.ColumnHeader>
                <Table.ColumnHeader>Duración</Table.ColumnHeader>
                <Table.ColumnHeader>Capacidad de referencia</Table.ColumnHeader>
              </Table.Row></Table.Header>
              <Table.Body>
                {visible.map((item) => (
                  <Table.Row key={item.id}>
                    <Table.Cell fontWeight="medium">{item.name}</Table.Cell>
                    <Table.Cell>{item.duration_minutes} min</Table.Cell>
                    <Table.Cell>{item.default_capacity} lugares</Table.Cell>
                  </Table.Row>
                ))}
              </Table.Body>
            </Table.Root>
          </Box>
          <SimpleGrid columns={1} gap={3} display={{ base: 'grid', md: 'none' }}>
            {visible.map((item) => (
              <Box key={item.id} bg="white" borderWidth="1px" borderRadius="lg" p={4}>
                <Text fontWeight="semibold">{item.name}</Text>
                <Text fontSize="sm" color="gray.600" mt={2}>
                  {item.duration_minutes} minutos · {item.default_capacity} lugares de referencia
                </Text>
              </Box>
            ))}
          </SimpleGrid>
          <HStack justify="flex-end" mt={3}>
            <Text fontSize="sm" color="gray.600" aria-live="polite">
              Mostrando {visible.length} de {data.length} clases recibidas.
            </Text>
          </HStack>
        </>
      )}
    </Box>
  );
};

export default CrudClassesPage;
