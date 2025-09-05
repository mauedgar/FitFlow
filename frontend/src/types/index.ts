// --- TIPOS PARA PROFESORES (Teachers) ---

/**
 * Representa el perfil público de un profesor.
 * Corresponde al schema `Teacher` y `TeacherInClassResponse` del backend.
 */
export interface TeacherProfile {
  id: string;
  name: string;
  surname: string;
  passport?: string;
  address?: string;
  bio?: string;
  cuil?: string;
  // No incluimos 'classes' para evitar redundancia en la mayoría de los casos
}

/**
 * Representa los datos necesarios para crear un perfil de profesor.
 * Corresponde al schema `TeacherCreate` del backend.
 */
export interface TeacherCreatePayload {
  name: string;
  surname: string;
  passport?: string;
  address?: string;
  bio?: string;
  cuil?: string;
}


// --- TIPOS PARA CLASES DE GIMNASIO (Gym Classes) ---

/**
 * Representa una clase de gimnasio completa, incluyendo sus profesores.
 * Corresponde al schema `GymClass` del backend.
 */
export interface GymClass {
  id: string;
  name: string;
  description: string;
  duration_minutes: number;
  difficulty: 'Principante' | 'Intermedio' | 'Avanzado'; // Ajusta a tus valores
  schedule: string; // Fecha en formato ISO string
  teachers: TeacherProfile[];
}

/**
 * Representa los datos necesarios para crear una nueva clase.
 * Corresponde al schema `GymClassCreate` del backend.
 */
export interface GymClassCreatePayload {
  name: string;
  description: string;
  duration_minutes: number;
  difficulty: 'Principante' | 'Intermedio' | 'Avanzado';
  schedule: string; // Fecha en formato ISO string
  teacher_ids: string[]; // Lista de UUIDs
}