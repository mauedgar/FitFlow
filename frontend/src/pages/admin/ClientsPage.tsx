import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Alert, Badge, Box, Button, Center, Heading, HStack, Input,
  SimpleGrid, Skeleton, Stack, Table, Text, VStack,
} from '@chakra-ui/react';
import { LuRefreshCw, LuSearch } from 'react-icons/lu';
import { useAuth } from '../../context/useAuth';
import { getAdminClients, type AdminClientSummary } from '../../services/clientService';

const matches = (client: AdminClientSummary, term: string) =>
  [client.full_name, client.email, client.phone ?? '']
    .some((field) => field.toLocaleLowerCase().includes(term));

const ClientsPage = () => {
  const { currentUser } = useAuth();
  const [search, setSearch] = useState('');
  const { data = [], isLoading, isError, isFetching, refetch } = useQuery({
    // Partition cached results by authenticated account, not only by page.
    queryKey: ['adminClients', currentUser?.email, 0, 100],
    queryFn: ({ signal }) => getAdminClients(signal),
    enabled: currentUser?.role === 'admin',
    retry: 1,
  });
  const normalizedSearch = search.trim().toLocaleLowerCase();
  const visibleClients = useMemo(
    () => data.filter((client) => matches(client, normalizedSearch)),
    [data, normalizedSearch],
  );

  return (
    <Box maxW="1200px" mx="auto">
      <Stack direction={{ base: 'column', md: 'row' }} gap={4}
        justify="space-between" align={{ base: 'stretch', md: 'center' }} mb={7}>
        <Box>
          <Heading as="h1" size="lg">Clientes</Heading>
          <Text color="gray.600" mt={1}>Consultá los clientes registrados del gimnasio.</Text>
        </Box>
        <Badge alignSelf={{ base: 'start', md: 'center' }} colorPalette="teal" px={3} py={1}>
          {isError ? 'No disponible' : isLoading ? 'Cargando…' : `${data.length} clientes en esta página`}
        </Badge>
      </Stack>

      <Box bg="white" borderWidth="1px" borderColor="gray.200" borderRadius="xl"
        p={{ base: 4, md: 5 }} boxShadow="sm" mb={4}>
        <Stack direction={{ base: 'column', sm: 'row' }}
          align={{ base: 'stretch', sm: 'center' }} gap={3}>
          <Box position="relative" flex="1">
            <Box position="absolute" left={3} top="50%" transform="translateY(-50%)"
              pointerEvents="none" color="gray.500" zIndex={1}>
              <LuSearch aria-hidden="true" />
            </Box>
            <Input
              pl={10}
              aria-label="Buscar clientes de esta página"
              placeholder="Buscar por nombre, correo o teléfono"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              disabled={isLoading || isError}
            />
          </Box>
          <Button onClick={() => void refetch()} loading={isFetching}
            variant="outline" colorPalette="teal">
            <LuRefreshCw aria-hidden="true" />Actualizar
          </Button>
        </Stack>
        <Text color="gray.500" fontSize="xs" mt={2}>
          La búsqueda filtra únicamente los primeros 100 registros recibidos.
        </Text>
      </Box>

      {isError ? (
        <Alert.Root status="error" borderRadius="lg" role="alert">
          <Alert.Indicator />
          <Alert.Content>
            <Alert.Title>No pudimos cargar los clientes.</Alert.Title>
            <Alert.Description>Comprobá la conexión y volvé a intentar.</Alert.Description>
          </Alert.Content>
        </Alert.Root>
      ) : isLoading ? (
        <Stack gap={3} role="status" aria-label="Cargando clientes">
          <Skeleton height="56px" borderRadius="md" />
          <Skeleton height="56px" borderRadius="md" />
          <Skeleton height="56px" borderRadius="md" />
          <Text>Consultando clientes…</Text>
        </Stack>
      ) : visibleClients.length === 0 ? (
        <Center borderWidth="1px" bg="white" borderColor="gray.200"
          borderRadius="xl" py={12} px={5}>
          <VStack textAlign="center" gap={2}>
            <Heading as="h2" size="md">
              {data.length === 0 ? 'Todavía no hay clientes registrados' : 'No encontramos coincidencias'}
            </Heading>
            <Text color="gray.600">
              {data.length === 0
                ? 'Los clientes aparecerán aquí cuando existan en el sistema.'
                : 'Probá con otro nombre, correo o teléfono.'}
            </Text>
            {normalizedSearch && (
              <Button size="sm" variant="plain" colorPalette="teal" onClick={() => setSearch('')}>
                Limpiar búsqueda
              </Button>
            )}
          </VStack>
        </Center>
      ) : (
        <>
          <Box display={{ base: 'none', md: 'block' }} overflowX="auto"
            bg="white" borderWidth="1px" borderColor="gray.200"
            borderRadius="xl" boxShadow="sm">
            <Table.Root variant="line" size="md">
              <Table.Header>
                <Table.Row>
                  <Table.ColumnHeader>Nombre</Table.ColumnHeader>
                  <Table.ColumnHeader>Correo electrónico</Table.ColumnHeader>
                  <Table.ColumnHeader>Teléfono</Table.ColumnHeader>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {visibleClients.map((client) => (
                  <Table.Row key={client.id}>
                    <Table.Cell fontWeight="medium">{client.full_name}</Table.Cell>
                    <Table.Cell>{client.email}</Table.Cell>
                    <Table.Cell>{client.phone || 'No informado'}</Table.Cell>
                  </Table.Row>
                ))}
              </Table.Body>
            </Table.Root>
          </Box>
          <SimpleGrid columns={1} gap={3} display={{ base: 'grid', md: 'none' }}>
            {visibleClients.map((client) => (
              <Box key={client.id} bg="white" borderWidth="1px" borderColor="gray.200"
                borderRadius="lg" p={4} boxShadow="sm">
                <Text fontWeight="semibold" mb={2}>{client.full_name}</Text>
                <Text fontSize="sm" overflowWrap="anywhere">{client.email}</Text>
                <Text color="gray.600" fontSize="sm" mt={1}>
                  {client.phone || 'Teléfono no informado'}
                </Text>
              </Box>
            ))}
          </SimpleGrid>
          <HStack mt={3} justify="flex-end">
            <Text fontSize="sm" color="gray.500" aria-live="polite">
              Mostrando {visibleClients.length} de {data.length} clientes recibidos.
            </Text>
          </HStack>
        </>
      )}
    </Box>
  );
};

export default ClientsPage;
