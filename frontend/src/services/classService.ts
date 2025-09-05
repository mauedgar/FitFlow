import apiClient from './api';
import { type GymClass, type GymClassCreatePayload } from '../types';

/**
 * Obtiene la lista completa de clases de gimnasio.
 */
const getAllClasses = async (): Promise<GymClass[]> => {
  try {
    const response = await apiClient.get<GymClass[]>('/gym-classes/');
    return response.data;
  } catch (error) {
    console.error('Error al obtener la lista de clases:', error);
    throw new Error('No se pudieron cargar las clases.');
  }
};

/**
 * Obtiene una clase de gimnasio específica por su ID.
 * @param classId - El UUID de la clase a obtener.
 */
const getClassById = async (classId: string): Promise<GymClass> => {
  try {
    const response = await apiClient.get<GymClass>(`/gym-classes/${classId}`);
    return response.data;
  } catch (error) {
    console.error(`Error al obtener la clase con ID ${classId}:`, error);
    throw new Error('No se pudo cargar la clase.');
  }
};

/**
 * Crea una nueva clase de gimnasio.
 * @param payload - Los datos de la clase a crear.
 */
const createClass = async (payload: GymClassCreatePayload): Promise<GymClass> => {
  try {
    const response = await apiClient.post<GymClass>('/gym-classes/', payload);
    return response.data;
  } catch (error) {
    console.error('Error al crear la clase:', error);
    throw new Error('No se pudo crear la clase.');
  }
};

const classService = {
  getAllClasses,
  getClassById,
  createClass,
};

export default classService;