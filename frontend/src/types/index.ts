// src/types/index.ts (Refactorizado y Completo)

// --- Enums ---
export enum UserRole {
  ADMIN = "admin",
  TRAINER = "trainer",
  CLIENT = "client",
}

export enum DifficultyLevel {
  BEGINNER = "Principante",
  INTERMEDIATE = "Intermedio",
  ADVANCED = "Avanzado",
}

export enum BookingStatus {
  CONFIRMED = "CONFIRMED",
  CANCELLED = "CANCELLED",
  PENDING = "PENDING",
}

// --- Schemas Base --- (si se usan en el frontend para herencia de Pydantic)
// Aunque en TypeScript no se "hereda" igual, puedes usar interfaces base.
export interface PersonBase {
  name: string;
  surname: string;
  passport?: string;
  address?: string;
  medical_fit_url?: string;
  profile_img_url?: string;
}

// --- User ---
// El usuario autenticado, con la información del token y su rol.
export interface User {
  id?: string; // Puede no estar en el token, se obtiene de otro endpoint
  email: string;
  role: UserRole;
  is_active?: boolean;
  // Otros campos del User si los necesitas en el frontend y los obtienes
}

// --- Token Payloads ---
export interface TokenPayload {
  sub: string;      // Email del usuario (subject)
  role: UserRole; // Rol del usuario
  exp: number;      // Expiración del token (timestamp)
}

export interface TokenResponse { // Para la respuesta del endpoint /login/token
  access_token: string;
  token_type: string;
}

// --- Teacher ---
// Esquema ligero para cuando un Teacher es anidado en otra respuesta (ej. ClassSchedule)
export interface TeacherInResponse extends PersonBase {
  id: string;
  bio?: string;
  cuil?: string;
  // Si en el backend, TeacherInClassScheduleResponse no incluye name, surname, etc.
  // entonces esta interfaz debería ser más minimalista.
}

// Esquema completo para un Teacher (ej. en un endpoint GET /teachers/{id})
export interface Teacher extends TeacherInResponse {
  // Aquí irían las relaciones si se cargan completas, ej.
  class_schedules: ClassScheduleInResponse[];
}

// --- GymClass ---
// Esquema ligero para cuando GymClass es anidado en otra respuesta (ej. ClassSchedule)
export interface GymClassInResponse {
  id: string;
  name: string;
  description: string;
  duration_minutes: number;
  difficulty: DifficultyLevel;
  default_capacity: number;
}

// Esquema completo para una GymClass (ej. en un endpoint GET /gym_classes/{id})
export interface GymClass {
  id: string;
  name: string;
  description: string;
  duration_minutes: number;
  difficulty: DifficultyLevel;
  default_capacity: number;
  // La clave aquí es que ahora las relaciones de horario y profesor van via ClassSchedule
  class_schedules: ClassScheduleInResponse[]; // Lista de ofertas de horarios recurrentes
  teachers?: TeacherInResponse[]; // Si aún mantienes una relación directa en el backend para otros fines
}

// Representa los datos necesarios para crear una nueva clase (sin profesores directamente)
export interface GymClassCreatePayload {
  name: string;
  description: string;
  duration_minutes: number;
  difficulty: DifficultyLevel;
  default_capacity: number; // Nuevo campo
}


// --- ClassSchedule ---
// Datos base de una oferta de horario recurrente
export interface ClassScheduleBase {
  days_of_week: number[]; // Array de números (0=Lunes, 6=Domingo)
  start_time: string;     // String "HH:MM:SS"
  end_time: string;       // String "HH:MM:SS"
  max_capacity: number;
  start_date: string;     // String "YYYY-MM-DD"
  end_date?: string;      // String "YYYY-MM-DD"
}

// Esquema de respuesta completo para una ClassSchedule
export interface ClassScheduleInResponse extends ClassScheduleBase {
  id: string;
  gym_class_id: string;
  teacher_id: string;
  gym_class: GymClassInResponse;      // Objeto GymClass anidado (versión ligera)
  teacher: TeacherInResponse;         // Objeto Teacher anidado (versión ligera)
  // future_sessions?: ClassSessionInResponse[]; // Puede ser cargado por separado
}
export interface ClassScheduleWithNextSession extends ClassScheduleInResponse {
  next_upcoming_session: {
    start_datetime: string;
    available_spots: number;
  } | null;
}

// --- ClassSession ---
// Datos base de una sesión de clase específica
export interface ClassSessionBase {
  start_datetime: string; // ISO String de fecha y hora
  end_datetime: string;   // ISO String de fecha y hora
  is_cancelled: boolean;
}

// Esquema de respuesta completo para una ClassSession
export interface ClassSession extends ClassSessionBase {
  id: string;
  class_schedule_id: string;
  class_schedule: ClassScheduleInResponse; // Objeto ClassSchedule anidado
  bookings: BookingInClassSessionResponse[]; // Lista de bookings para esta sesión
  current_bookings_count: number; // Campo calculado en el backend
  available_spots: number;        // Campo calculado en el backend
  is_booked_by_current_user?: boolean; // Campo auxiliar para el frontend
}

// Esquema ligero para cuando ClassSession es anidada (ej. en Booking)
export interface ClassSessionInBookingResponse extends ClassSessionBase {
  id: string;
  class_schedule_id: string; // Mantener el ID para referencia
  // Puedes incluir más campos si necesitas detalles de la sesión dentro de la reserva
  class_schedule: { // Aquí puedes poner una versión aún más ligera de ClassSchedule si solo necesitas nombre de clase/profesor
    gym_class: { name: string; duration_minutes: number; };
    teacher: { name: string; surname: string; };
  };
}

// --- Booking ---
// Datos base de una reserva
export interface BookingBase {
  status: BookingStatus;
}

// Esquema de respuesta para una reserva (ej. para la lista de mis reservas)
export interface Booking extends BookingBase {
  id: string;
  client_id: string;
  class_session_id: string;
  booking_date: string; // ISO String
  // Objetos anidados para mostrar detalles de la sesión y cliente
  client: ClientInBookingResponse;
  class_session: ClassSessionInBookingResponse; // Usar la versión ligera o completa según necesidad
}

// Esquema ligero para cuando Booking es anidado (ej. en ClassSession o Client)
export interface BookingInClassSessionResponse extends BookingBase {
  id: string;
  client_id: string;
  booking_date: string;
}


// --- Client ---
// Esquema ligero para cuando Client es anidado (ej. en Booking)
export interface ClientInBookingResponse extends PersonBase {
  id: string;
}

// Esquema completo para un Client
export interface Client extends PersonBase {
  id: string;
  user_id: string;
  // bookings: BookingInClientResponse[]; // Si quieres cargar las reservas aquí
}

// --- Payload para crear una reserva ---
export interface BookingCreatePayload {
  class_session_id?: string;
  class_schedule_id?: string;
}

export interface FastAPIValidationError {
  loc: (string | number)[]; // Puede ser ['body', 'field_name'] o ['query', 0, 'sub_field']
  msg: string;
  type: string;
}
export interface FastAPIErrorResponse {
  detail: string | Array<{ loc: (string | number)[], msg: string, type: string }>;
}
// También puedes querer una interfaz para un error 401 si tu backend lo devuelve diferente
export interface FastAPIAuthErrorResponse {
  detail: string; // Para errores como "Email o contraseña incorrectos"
}
