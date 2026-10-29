import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Alert, AlertIcon, Badge, Box, Button, Center, Heading, HStack, Input,
  InputGroup, InputLeftElement, SimpleGrid, Skeleton, Stack, Table,
  Tbody, Td, Text, Th, Thead, Tr, VStack,
} from '@chakra-ui/react';
import { SearchIcon, RepeatIcon } from '@chakra-ui/icons';
import { getAdminClients, type AdminClientSummary } from '../../services/clientService';

const matches = (client: AdminClientSummary, term: string) =>
  [client.full_name, client.email, client.phone ?? '']
    .some((field) => field.toLocaleLowerCase().includes(term));

const ClientsPage = () => {
  const [search, setSearch] = useState('');
  const { data = [], isLoading, isError, isFetching, refetch } = useQuery({
    queryKey: ['adminClients', 0, 100],
    queryFn: getAdminClients,
    retry: 1,
  });
  const normalizedSearch = search.trim().toLocaleLowerCase();
  const visibleClients = useMemo(
    () => data.filter((client) => matches(client, normalizedSearch)),
    [data, normalizedSearch],
  );

  return (
    <Box maxW="1200px" mx="auto">
      <Stack direction={{ base: 'column', md: 'row' }} spacing={4}
        justify="space-between" align={{ base: 'stretch', md: 'center' }} mb={7}>
        <Box>
          <Heading as="h1" size="lg">Clientes</Heading>
          <Text color="gray.600" mt={1}>
            Consultá los clientes registrados del gimnasio.
          </Text>
        </Box>
        <Badge alignSelf={{ base: 'start', md: 'center' }} colorScheme="teal" px={3} py={1} borderRadius="md">
          {isLoading ? 'Cargando…' : `${data.length} clientes en esta página`}
        </Badge>
      </Stack>

      <Box bg="white" borderWidth="1px" borderColor="gray.200" borderRadius="xl" p={{ base: 4, md: 5 }}
        boxShadow="sm" mb={4}>
        <Stack direction={{ base: 'column', sm: 'row' }} align={{ base: 'stretch', sm: 'center' }} spacing={3}>
          <InputGroup flex="1">
            <InputLeftElement pointerEvents="none"><SearchIcon color="gray.400" /></InputLeftElement>
            <Input
              aria-label="Buscar clientes de esta página"
              placeholder="Buscar por nombre, correo o teléfono"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              isDisabled={isLoading || isError}
            />
          </InputGroup>
          <Button leftIcon={<RepeatIcon />} onClick={() => void refetch()}
            isLoading={isFetching} variant="outline" colorScheme="teal">
            Actualizar
          </Button>
        </Stack>
        <Text color="gray.500" fontSize="xs" mt={2}>
          La búsqueda filtra únicamente los primeros 100 registros recibidos.
        </Text>
      </Box>

      {isError ? (
        <Alert status="error" borderRadius="lg" role="alert">
          <AlertIcon />
          <VStack align="start" spacing={1}>
            <Text fontWeight="semibold">No pudimos cargar los clientes.</Text>
            <Text fontSize="sm">Comprobá la conexión y volvé a intentar.</Text>
          </VStack>
        </Alert>
      ) : isLoading ? (
        <Stack spacing={3} aria-label="Cargando clientes">
          <Skeleton height="56px" borderRadius="md" />
          <Skeleton height="56px" borderRadius="md" />
          <Skeleton height="56px" borderRadius="md" />
        </Stack>
      ) : visibleClients.length === 0 ? (
        <Center borderWidth="1px" bg="white" borderColor="gray.200" borderRadius="xl" py={12} px={5}>
          <VStack textAlign="center" spacing={2}>
            <Heading as="h2" size="md">
              {data.length === 0 ? 'Todavía no hay clientes registrados' : 'No encontramos coincidencias'}
            </Heading>
            <Text color="gray.600">
              {data.length === 0
                ? 'Los clientes aparecerán aquí cuando existan en el sistema.'
                : 'Probá con otro nombre, correo o teléfono.'}
            </Text>
            {normalizedSearch && (
              <Button size="sm" variant="link" colorScheme="teal" onClick={() => setSearch('')}>
                Limpiar búsqueda
              </Button>
            )}
          </VStack>
        </Center>
      ) : (
        <>
          <Box display={{ base: 'none', md: 'block' }} overflowX="auto" bg="white"
            borderWidth="1px" borderColor="gray.200" borderRadius="xl" boxShadow="sm">
            <Table variant="simple" size="md">
              <Thead bg="gray.50">
                <Tr>
                  <Th>Nombre</Th>
                  <Th>Correo electrónico</Th>
                  <Th>Teléfono</Th>
                </Tr>
              </Thead>
              <Tbody>
                {visibleClients.map((client) => (
                  <Tr key={client.id}>
                    <Td fontWeight="medium">{client.full_name}</Td>
                    <Td>{client.email}</Td>
                    <Td>{client.phone || 'No informado'}</Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </Box>
          <SimpleGrid columns={1} spacing={3} display={{ base: 'grid', md: 'none' }}>
            {visibleClients.map((client) => (
              <Box key={client.id} bg="white" borderWidth="1px" borderColor="gray.200"
                borderRadius="lg" p={4} boxShadow="sm">
                <Text fontWeight="semibold" mb={2}>{client.full_name}</Text>
                <Text fontSize="sm" overflowWrap="anywhere">{client.email}</Text>
                <Text color="gray.600" fontSize="sm" mt={1}>{client.phone || 'Teléfono no informado'}</Text>
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
