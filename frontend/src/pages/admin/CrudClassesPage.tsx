import {
  Box,
  Heading,
  Button,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  IconButton,
  HStack,
  Badge,
  VStack,
  Text,
  useToast
} from '@chakra-ui/react';
import { AddIcon, EditIcon, DeleteIcon } from '@chakra-ui/icons';

// Datos de ejemplo
const clientsData = [
  { id: 1, name: 'Juan Pérez', email: 'juan.perez@email.com', status: 'Activo' },
  { id: 2, name: 'Ana Gómez', email: 'ana.gomez@email.com', status: 'Inactivo' },
  { id: 3, name: 'Carlos Ruiz', email: 'carlos.ruiz@email.com', status: 'Activo' },
];

const ClassesPage = () => {
  const toast = useToast();

  const handleAdd = () => toast({ title: "Funcionalidad 'Añadir' no implementada.", status: 'info' });
  const handleEdit = (id: number) => toast({ title: `Funcionalidad 'Editar' cliente ${id} no implementada.`, status: 'info' });
  const handleDelete = (id: number) => toast({ title: `Funcionalidad 'Eliminar' cliente ${id} no implementada.`, status: 'warning' });

  return (
    <Box>
      <HStack justifyContent="space-between" mb={6}>
        <Heading as="h1" size="lg">Gestionar Clientes</Heading>
        <Button leftIcon={<AddIcon />} colorScheme="teal" onClick={handleAdd}>
          Añadir Cliente
        </Button>
      </HStack>

      {/* --- VISTA DE TABLA PARA ESCRITORIO --- */}
      <Box display={{ base: 'none', md: 'block' }} bg="white" borderRadius="md" boxShadow="md">
        <Table variant="simple">
          <Thead>
            <Tr>
              <Th>Nombre</Th>
              <Th>Email</Th>
              <Th>Estado</Th>
              <Th>Acciones</Th>
            </Tr>
          </Thead>
          <Tbody>
            {clientsData.map((client) => (
              <Tr key={client.id}>
                <Td>{client.name}</Td>
                <Td>{client.email}</Td>
                <Td>
                  <Badge colorScheme={client.status === 'Activo' ? 'green' : 'red'}>
                    {client.status}
                  </Badge>
                </Td>
                <Td>
                  <HStack spacing={2}>
                    <IconButton icon={<EditIcon />} aria-label="Editar cliente" size="sm" onClick={() => handleEdit(client.id)} />
                    <IconButton icon={<DeleteIcon />} aria-label="Eliminar cliente" size="sm" colorScheme="red" onClick={() => handleDelete(client.id)} />
                  </HStack>
                </Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      </Box>

      {/* --- VISTA DE TARJETAS PARA MÓVIL --- */}
      <VStack spacing={4} display={{ base: 'block', md: 'none' }}>
        {clientsData.map((client) => (
          <Box key={client.id} p={4} bg="white" borderRadius="md" boxShadow="md" w="full">
            <HStack justifyContent="space-between">
              <Text fontWeight="bold">{client.name}</Text>
              <Badge colorScheme={client.status === 'Activo' ? 'green' : 'red'}>
                {client.status}
              </Badge>
            </HStack>
            <Text fontSize="sm" color="gray.500">{client.email}</Text>
            <HStack spacing={2} mt={4} justifyContent="flex-end">
              <IconButton icon={<EditIcon />} aria-label="Editar cliente" size="sm" onClick={() => handleEdit(client.id)} />
              <IconButton icon={<DeleteIcon />} aria-label="Eliminar cliente" size="sm" colorScheme="red" onClick={() => handleDelete(client.id)} />
            </HStack>
          </Box>
        ))}
      </VStack>
    </Box>
  );
};

export default ClassesPage;