import {
  Avatar,
  Button,
  Flex,
  HStack,
  Icon,
  Menu,
  MenuButton,
  MenuDivider,
  MenuItem,
  MenuList,
  Spacer,
  Text,
} from '@chakra-ui/react';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/useAuth';
import {
  FiHome,
  FiUsers,
  FiLogOut,
  FiBriefcase,
  FiClipboard,
  FiBookOpen,
  FiBarChart2,
  FiCalendar,
  FiSettings,
  FiDollarSign,
} from 'react-icons/fi';
import { ChevronDownIcon } from '@chakra-ui/icons';

// Configuración de menús para fácil mantenimiento y escalabilidad
const adminMenus = [
  {
    label: "Clientes",
    icon: FiUsers,
    subitems: [
      { label: "Ver Clientes", to: "/admin/clients", icon: FiUsers },
      { label: "Agregar Cliente", to: "/admin/clients/create", icon: FiUsers },
      { label: "Membresías", to: "/admin/clients/memberships", icon: FiUsers },
    ]
  },
  {
    label: "Profesores",
    icon: FiBriefcase,
    subitems: [
      { label: "Ver Profesores", to: "/admin/teachers", icon: FiBriefcase },
      { label: "Agregar Profesor", to: "/admin/teachers/create", icon: FiBriefcase },
      { label: "Horarios", to: "/admin/teachers/schedules", icon: FiBriefcase },
    ]
  },
  {
    label: "Clases",
    icon: FiClipboard,
    subitems: [
      { label: "Gestionar Clases", to: "/admin/classes", icon: FiClipboard },
      { label: "Crear Nueva Clase", to: "/admin/classes/create", icon: FiClipboard },
      { label: "Programar Horarios", to: "/admin/classes/schedules", icon: FiClipboard },
    ]
  },
  {
    label: "Reservas",
    icon: FiBookOpen,
    subitems: [
      { label: "Ver Reservas", to: "/admin/bookings", icon: FiBookOpen },
      { label: "Lista de Espera", to: "/admin/bookings/waitlist", icon: FiBookOpen },
      { label: "Cancelaciones", to: "/admin/bookings/cancelled", icon: FiBookOpen },
    ]
  },
  {
    label: "Informes",
    icon: FiBarChart2,
    subitems: [
      { label: "Alumnos por Clase", to: "/admin/reports/attendance", icon: FiBarChart2 },
      { label: "Clases Populares", to: "/admin/reports/popular-classes", icon: FiBarChart2 },
      { label: "Ingresos Mensuales", to: "/admin/reports/revenue", icon: FiBarChart2 },
      { label: "Ocupación de Horarios", to: "/admin/reports/schedule-usage", icon: FiBarChart2 },
    ]
  },
  {
    label: "Calendario",
    icon: FiCalendar,
    subitems: [
      { label: "Vista Semanal", to: "/admin/calendar/weekly", icon: FiCalendar },
      { label: "Vista Mensual", to: "/admin/calendar/monthly", icon: FiCalendar },
      { label: "Eventos Especiales", to: "/admin/calendar/events", icon: FiCalendar },
    ]
  },
  {
    label: "Herramientas",
    icon: FiSettings,
    subitems: [
      { label: "Envío Masivo Email", to: "/admin/tools/bulk-email", icon: FiSettings },
      { label: "Check-in Manual", to: "/admin/tools/manual-checkin", icon: FiSettings },
      { label: "Backup de Datos", to: "/admin/tools/backup", icon: FiSettings },
      { label: "Configuración", to: "/admin/tools/settings", icon: FiSettings },
    ]
  },
  {
    label: "Facturación",
    icon: FiDollarSign,
    subitems: [
      { label: "Ver Facturas", to: "/admin/billing/invoices", icon: FiDollarSign },
      { label: "Pagos Pendientes", to: "/admin/billing/pending", icon: FiDollarSign },
      { label: "Descuentos", to: "/admin/billing/discounts", icon: FiDollarSign },
    ]
  },
];

const AdminNavBar: React.FC = () => {
  const { currentUser, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <Flex
      as="header"
      align="center"
      justify="space-between"
      w="100%"
      px="4"
      py="2"
      bg="white"
      borderBottomWidth="1px"
      borderColor="gray.200"
      h="64px"
      boxShadow="sm"
    >
      {/* DASHBOARD BUTTON */}
      <Button
        as={RouterLink}
        to="/admin"
        leftIcon={<Icon as={FiHome} />}
        variant="ghost"
        colorScheme="teal"
        size="md"
      >
        Dashboard
      </Button>

      <Spacer />

      {/* MENÚS CRUD Y GESTIÓN */}
      <HStack spacing="2" overflowX="auto">
        {adminMenus.map((menu) => (
          <Menu key={menu.label}>
            <MenuButton
              as={Button}
              rightIcon={<ChevronDownIcon />}
              variant="ghost"
              size="sm"
              minW="max-content"
            >
              <HStack spacing="1">
                <Icon as={menu.icon} />
                <Text>{menu.label}</Text>
              </HStack>
            </MenuButton>
            <MenuList>
              {menu.subitems.map((item) => (
                <MenuItem
                  key={item.to}
                  as={RouterLink}
                  to={item.to}
                  icon={<Icon as={item.icon} />}
                >
                  {item.label}
                </MenuItem>
              ))}
            </MenuList>
          </Menu>
        ))}
      </HStack>

      <Spacer />

      {/* PERFIL Y LOGOUT */}
      <Menu>
        <MenuButton as={Button} variant="ghost" p={2} rounded="full">
          <HStack spacing="2">
            <Avatar size="sm" name={currentUser?.email || 'Admin'} />
            <Text display={{ base: 'none', lg: 'block' }} fontSize="sm" fontWeight="medium">
              {currentUser?.email || 'Administrador'}
            </Text>
            <ChevronDownIcon />
          </HStack>
        </MenuButton>
        <MenuList>
          <MenuItem as={RouterLink} to="/admin/profile">
            Mi Perfil
          </MenuItem>
          <MenuItem as={RouterLink} to="/admin/settings">
            Configuración
          </MenuItem>
          <MenuDivider />
          <MenuItem
            onClick={handleLogout}
            color="red.500"
            icon={<Icon as={FiLogOut} />}
          >
            Cerrar Sesión
          </MenuItem>
        </MenuList>
      </Menu>
    </Flex>
  );
};

export default AdminNavBar;