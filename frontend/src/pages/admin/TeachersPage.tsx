import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Alert, Badge, Box, Button, Center, Heading, HStack, Input,
  SimpleGrid, Skeleton, Stack, Table, Text, VStack,
} from '@chakra-ui/react';
import { LuRefreshCw, LuSearch } from 'react-icons/lu';
import { useAuth } from '../../context/useAuth';
import { getAdminTeacherSummaries, type AdminTeacherSummary } from '../../services/adminReadService';

const matches = (teacher: AdminTeacherSummary, term: string) =>
  [teacher.full_name, teacher.first_name, teacher.last_name]
    .some((field) => field.toLocaleLowerCase().includes(term));

const TeachersPage = () => {
  const { currentUser } = useAuth();
  const [search, setSearch] = useState('');
  const { data = [], isLoading, isError, isFetching, refetch } = useQuery({
    queryKey: ['adminTeacherSummaries', currentUser?.email],
    queryFn: ({ signal }) => getAdminTeacherSummaries(signal),
    enabled: currentUser?.role === 'admin',
    retry: 1,
  });

  const term = search.trim().toLocaleLowerCase();
  const visible = useMemo(() => data.filter((teacher) => matches(teacher, term)), [data, term]);

  return (
    <Box maxW="1200px" mx="auto">
      <Stack direction={{ base: 'column', md: 'row' }} justify="space-between"
        align={{ base: 'stretch', md: 'center' }} gap={4} mb={6}>
        <Box>
          <Heading as="h1" size="lg">Profesores</Heading>
          <Text color="gray.600" mt={1}>Listado de perfiles públicos, sin datos personales reservados.</Text>
        </Box>
        <Badge colorPalette="teal" alignSelf={{ base: 'start', md: 'center' }}>
          {isError ? 'No disponible' : isLoading ? 'Cargando…' : `${data.length} perfiles recibidos`}
        </Badge>
      </Stack>
      <Stack direction={{ base: 'column', sm: 'row' }} mb={5} gap={3}>
        <Box flex="1" position="relative">
          <Box color="gray.500" position="absolute" left={3} top="50%"
            transform="translateY(-50%)" pointerEvents="none"><LuSearch aria-hidden="true" /></Box>
          <Input aria-label="Buscar profesores de los registros recibidos" pl={10}
            placeholder="Buscar por nombre" value={search}
            onChange={(event) => setSearch(event.target.value)}
            disabled={isLoading || isError} />
        </Box>
        <Button colorPalette="teal" variant="outline" loading={isFetching}
          onClick={() => void refetch()}><LuRefreshCw aria-hidden="true" />Actualizar</Button>
      </Stack>
      {isError ? (
        <Alert.Root status="error" borderRadius="lg" role="alert">
          <Alert.Indicator /><Alert.Content>
            <Alert.Title>No pudimos cargar los profesores.</Alert.Title>
            <Alert.Description>Comprobá la conexión y volvé a intentar.</Alert.Description>
          </Alert.Content>
        </Alert.Root>
      ) : isLoading ? (
        <Stack gap={3} role="status" aria-label="Cargando profesores">
          <Skeleton height="56px" /><Skeleton height="56px" /><Text>Consultando profesores…</Text>
        </Stack>
      ) : visible.length === 0 ? (
        <Center bg="white" borderWidth="1px" borderRadius="xl" p={10}>
          <VStack gap={3} textAlign="center">
            <Heading as="h2" size="md">
              {data.length === 0 ? 'Todavía no hay profesores disponibles' : 'No encontramos coincidencias'}
            </Heading>
            <Text color="gray.600">
              {data.length === 0 ? 'Los perfiles aparecerán aquí cuando existan en el sistema.' : 'Probá con otro nombre.'}
            </Text>
            {term && <Button variant="plain" colorPalette="teal" onClick={() => setSearch('')}>Limpiar búsqueda</Button>}
          </VStack>
        </Center>
      ) : (
        <>
          <Box display={{ base: 'none', md: 'block' }} bg="white"
            borderWidth="1px" borderRadius="xl" overflowX="auto">
            <Table.Root variant="line">
              <Table.Header><Table.Row>
                <Table.ColumnHeader>Profesor</Table.ColumnHeader>
                <Table.ColumnHeader>Presentación pública</Table.ColumnHeader>
              </Table.Row></Table.Header>
              <Table.Body>
                {visible.map((teacher) => (
                  <Table.Row key={teacher.id}>
                    <Table.Cell fontWeight="medium">{teacher.full_name}</Table.Cell>
                    <Table.Cell>{teacher.bio || 'Sin presentación disponible'}</Table.Cell>
                  </Table.Row>
                ))}
              </Table.Body>
            </Table.Root>
          </Box>
          <SimpleGrid columns={1} gap={3} display={{ base: 'grid', md: 'none' }}>
            {visible.map((teacher) => (
              <Box key={teacher.id} bg="white" borderWidth="1px" p={4} borderRadius="lg">
                <Text fontWeight="semibold">{teacher.full_name}</Text>
                <Text color="gray.600" fontSize="sm" mt={1}>
                  {teacher.bio || 'Sin presentación disponible'}
                </Text>
              </Box>
            ))}
          </SimpleGrid>
          <HStack justify="flex-end" mt={3}>
            <Text fontSize="sm" color="gray.600" aria-live="polite">
              Mostrando {visible.length} de {data.length} perfiles recibidos.
            </Text>
          </HStack>
        </>
      )}
    </Box>
  );
};

export default TeachersPage;
