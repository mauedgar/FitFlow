import apiClient from './api';
import { type TeacherProfile, type TeacherCreatePayload } from '../types';

/**
 * Obtiene la lista de todos los perfiles de profesores.
 */
const getAllTeachers = async (): Promise<TeacherProfile[]> => {
  try {
    const response = await apiClient.get<TeacherProfile[]>('/teachers/');
    return response.data;
  } catch (error) {
    console.error('Error al obtener la lista de profesores:', error);
    throw new Error('No se pudieron cargar los profesores.');
  }
};

/**
 * Obtiene el perfil de un profesor específico por su ID.
 * @param teacherId - El UUID del profesor a obtener.
 */
const getTeacherById = async (teacherId: string): Promise<TeacherProfile> => {
  try {
    const response = await apiClient.get<TeacherProfile>(`/teachers/${teacherId}`);
    return response.data;
  } catch (error) {
    console.error(`Error al obtener el profesor con ID ${teacherId}:`, error);
    throw new Error('No se pudo cargar el perfil del profesor.');
  }
};

/**
 * Crea un nuevo perfil de profesor para un usuario existente.
 * @param userId - El UUID del usuario al que se le creará el perfil.
 * @param payload - Los datos del perfil del profesor.
 */
const createTeacherProfile = async (userId: string, payload: TeacherCreatePayload): Promise<TeacherProfile> => {
  try {
    const response = await apiClient.post<TeacherProfile>(`/teachers/${userId}`, payload);
    return response.data;
  } catch (error) {
    console.error(`Error al crear el perfil de profesor para el usuario ${userId}:`, error);
    throw new Error('No se pudo crear el perfil del profesor.');
  }
};

const teacherService = {
  getAllTeachers,
  getTeacherById,
  createTeacherProfile,
};

export default teacherService;