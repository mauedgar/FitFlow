import { toaster } from '../../components/ui/toaster-store';
import {
  Box,
  Heading,
  Button,
  Table,
  IconButton,
  HStack,
  Badge,
  VStack,
  Text,

} from '@chakra-ui/react';
import { LuPencil, LuPlus, LuTrash2 } from 'react-icons/lu';

// Datos de ejemplo
const clientsData = [
  { id: 1, name: 'Juan Pérez', email: 'juan.perez@email.com', status: 'Activo' },
  { id: 2, name: 'Ana Gómez', email: 'ana.gomez@email.com', status: 'Inactivo' },
  { id: 3, name: 'Carlos Ruiz', email: 'carlos.ruiz@email.com', status: 'Activo' },
];

const ClientsPage = () => {

  const handleAdd = () => toaster.create({ title: "Funcionalidad 'Añadir' no implementada.", type: 'info' });
  const handleEdit = (id: number) => toaster.create({ title: `Funcionalidad 'Editar' cliente ${id} no implementada.`, type: 'info' });
  const handleDelete = (id: number) => toaster.create({ title: `Funcionalidad 'Eliminar' cliente ${id} no implementada.`, type: 'warning' });

  return (
    <Box>
      <HStack justifyContent="space-between" mb={6}>
        <Heading as="h1" size="lg">Gestionar Clientes</Heading>
        <Button colorPalette="teal" onClick={handleAdd}><LuPlus />Añadir Cliente
                  </Button>
      </HStack>

      {/* --- VISTA DE TABLA PARA ESCRITORIO --- */}
      <Box display={{ base: 'none', md: 'block' }} bg="white" borderRadius="md" boxShadow="md">
        <Table.Root variant="line">
          <Table.Header>
            <Table.Row>
              <Table.ColumnHeader>Nombre</Table.ColumnHeader>
              <Table.ColumnHeader>Email</Table.ColumnHeader>
              <Table.ColumnHeader>Estado</Table.ColumnHeader>
              <Table.ColumnHeader>Acciones</Table.ColumnHeader>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {clientsData.map((client) => (
              <Table.Row key={client.id}>
                <Table.Cell>{client.name}</Table.Cell>
                <Table.Cell>{client.email}</Table.Cell>
                <Table.Cell>
                  <Badge colorPalette={client.status === 'Activo' ? 'green' : 'red'}>
                    {client.status}
                  </Badge>
                </Table.Cell>
                <Table.Cell>
                  <HStack gap={2}>
                    <IconButton
                      aria-label="Editar cliente"
                      size="sm"
                      onClick={() => handleEdit(client.id)}><LuPencil /></IconButton>
                    <IconButton
                      aria-label="Eliminar cliente"
                      size="sm"
                      colorPalette="red"
                      onClick={() => handleDelete(client.id)}><LuTrash2 /></IconButton>
                  </HStack>
                </Table.Cell>
              </Table.Row>
            ))}
          </Table.Body>
        </Table.Root>
      </Box>

      {/* --- VISTA DE TARJETAS PARA MÓVIL --- */}
      <VStack gap={4} display={{ base: 'block', md: 'none' }}>
        {clientsData.map((client) => (
          <Box key={client.id} p={4} bg="white" borderRadius="md" boxShadow="md" w="full">
            <HStack justifyContent="space-between">
              <Text fontWeight="bold">{client.name}</Text>
              <Badge colorPalette={client.status === 'Activo' ? 'green' : 'red'}>
                {client.status}
              </Badge>
            </HStack>
            <Text fontSize="sm" color="gray.500">{client.email}</Text>
            <HStack gap={2} mt={4} justifyContent="flex-end">
              <IconButton
                aria-label="Editar cliente"
                size="sm"
                onClick={() => handleEdit(client.id)}><LuPencil /></IconButton>
              <IconButton
                aria-label="Eliminar cliente"
                size="sm"
                colorPalette="red"
                onClick={() => handleDelete(client.id)}><LuTrash2 /></IconButton>
            </HStack>
          </Box>
        ))}
      </VStack>
    </Box>
  );
};

export default ClientsPage;
