import { useQuery } from '@tanstack/react-query';
import {
  Alert, Badge, Box, Button, Heading, HStack, SimpleGrid,
  Skeleton, Stack, Text, VStack,
} from '@chakra-ui/react';
import { Link as RouterLink } from 'react-router-dom';
import { LuArrowRight, LuRefreshCw } from 'react-icons/lu';
import { useAuth } from '../../context/useAuth';
import { getAdminClients } from '../../services/clientService';
import { getAdminTeacherSummaries, getAdminGymClassSummaries } from '../../services/adminReadService';

interface SummaryCardProps {
  title: string;
  label: string;
  count: number | undefined;
  isLoading: boolean;
  isError: boolean;
  to: string;
}

const SummaryCard = ({ title, label, count, isLoading, isError, to }: SummaryCardProps) => (
  <Box bg="white" borderWidth="1px" borderColor="gray.200" borderRadius="xl"
    p={{ base: 4, md: 5 }} minW={0} boxShadow="sm">
    <Text color="gray.600" fontSize="sm">{title}</Text>
    {isLoading ? (
      <Skeleton height="40px" my={3} role="status" aria-label={`Cargando ${title}`} />
    ) : (
      <Heading as="h2" size="2xl" my={3} color={isError ? 'red.700' : 'gray.800'}>
        {isError || count === undefined ? 'No disponible' : count.toLocaleString('es-AR')}
      </Heading>
    )}
    <Text color="gray.600" fontSize="xs" mb={4}>{label}</Text>
    <Button colorPalette="teal" variant="outline" size="sm" asChild>
      <RouterLink to={to}>Ver sección <LuArrowRight aria-hidden="true" /></RouterLink>
    </Button>
  </Box>
);

const AdminDashboardPage = () => {
  const { currentUser, sessionGeneration } = useAuth();
  const adminEnabled = currentUser?.role === 'admin';

  const clients = useQuery({
    queryKey: ['adminClients', currentUser?.email, sessionGeneration, 0, 100],
    queryFn: ({ signal }) => getAdminClients(signal),
    enabled: adminEnabled,
    retry: 1,
  });
  const teachers = useQuery({
    queryKey: ['adminTeacherSummaries', currentUser?.email, sessionGeneration],
    queryFn: ({ signal }) => getAdminTeacherSummaries(signal),
    enabled: adminEnabled,
    retry: 1,
  });
  const classes = useQuery({
    queryKey: ['adminGymClassSummaries', currentUser?.email, sessionGeneration],
    queryFn: ({ signal }) => getAdminGymClassSummaries(signal),
    enabled: adminEnabled,
    retry: 1,
  });

  const isRefreshing = clients.isFetching || teachers.isFetching || classes.isFetching;
  const hasError = clients.isError || teachers.isError || classes.isError;
  const refresh = () => {
    void clients.refetch();
    void teachers.refetch();
    void classes.refetch();
  };

  return (
    <Box maxW="1200px" mx="auto">
      <Stack direction={{ base: 'column', sm: 'row' }} align={{ base: 'stretch', sm: 'center' }}
        justify="space-between" gap={3} mb={7}>
        <Box>
          <Heading as="h1" size="xl">Panel de administración</Heading>
          <Text color="gray.600" mt={2}>
            Información actual del gimnasio, consultada desde la API.
          </Text>
        </Box>
        <Button colorPalette="teal" variant="outline" onClick={refresh}
          loading={isRefreshing} disabled={!adminEnabled}>
          <LuRefreshCw aria-hidden="true" />Actualizar datos
        </Button>
      </Stack>

      {hasError && (
        <Alert.Root status="error" mb={5} borderRadius="lg" role="alert">
          <Alert.Indicator />
          <Alert.Content>
            <Alert.Title>Algunas secciones no respondieron</Alert.Title>
            <Alert.Description>
              Los datos no disponibles no se cuentan como cero. Podés volver a intentar.
            </Alert.Description>
          </Alert.Content>
        </Alert.Root>
      )}
      <SimpleGrid columns={{ base: 1, md: 3 }} gap={4}>
        <SummaryCard title="Clientes" label="Registros recibidos en la primera página (máximo 100); no es el total general."
          count={clients.data?.length} isLoading={clients.isLoading}
          isError={clients.isError} to="/admin/clients" />
        <SummaryCard title="Profesores" label="Perfiles devueltos por el listado público; no es un total certificado."
          count={teachers.data?.length} isLoading={teachers.isLoading}
          isError={teachers.isError} to="/admin/teachers" />
        <SummaryCard title="Clases" label="Clases devueltas por el catálogo público; no es un total certificado."
          count={classes.data?.length} isLoading={classes.isLoading}
          isError={classes.isError} to="/admin/classes" />
      </SimpleGrid>
      <Box mt={7} bg="white" borderWidth="1px" borderColor="gray.200"
        borderRadius="xl" p={{ base: 4, md: 6 }}>
        <HStack justify="space-between" align="start" gap={3} flexWrap="wrap">
          <VStack gap={2} align="start">
            <Heading as="h2" size="md">Accesos rápidos</Heading>
            <Text color="gray.600" fontSize="sm">
              Consultá los registros actuales; las altas y modificaciones todavía no están habilitadas.
            </Text>
          </VStack>
          <Badge colorPalette="teal">Solo lectura</Badge>
        </HStack>
        <SimpleGrid columns={{ base: 1, sm: 3 }} gap={3} mt={5}>
          {[
            { label: 'Consultar clientes', to: '/admin/clients' },
            { label: 'Consultar profesores', to: '/admin/teachers' },
            { label: 'Consultar clases', to: '/admin/classes' },
          ].map((item) => (
            <Button key={item.to} asChild variant="subtle" colorPalette="teal"
              justifyContent="space-between">
              <RouterLink to={item.to}>{item.label}<LuArrowRight aria-hidden="true" /></RouterLink>
            </Button>
          ))}
        </SimpleGrid>
      </Box>
    </Box>
  );
};

export default AdminDashboardPage;
