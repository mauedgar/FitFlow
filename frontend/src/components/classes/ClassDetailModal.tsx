import React from 'react';
import {
  Modal, ModalOverlay, ModalContent, ModalHeader, ModalBody, ModalCloseButton,
} from '@chakra-ui/react';
import { useQuery } from '@tanstack/react-query'; // ¡El protagonista!
import classService  from '../../services/classService';
import ClassDetailView  from './ClassDetailView';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorDisplay from '../common/ErrorDisplay';

interface ClassDetailModalProps {
  classId: string | null;
  isOpen: boolean;
  onClose: () => void;
}

const ClassDetailModal: React.FC<ClassDetailModalProps> = ({ classId, isOpen, onClose }) => {
  // --- TANSTACK QUERY EN SU MÁXIMA EXPRESIÓN ---
  const { data: gymClass, isLoading, isError } = useQuery({
    // 1. Query Key Dinámica: La clave incluye el 'classId'. Esto significa que
    // TanStack Query cacheará los detalles de cada clase individualmente. Si
    // cierras y vuelves a abrir el modal de la misma clase, los datos serán
    // instantáneos desde la caché.
    queryKey: ['class', classId],

    // 2. Función de Fetching: Solo se ejecutará si la query está "enabled".
    queryFn: () => {
      // Usamos '!' para decirle a TypeScript que, en este punto, sabemos que
      // classId no será null, gracias a la opción 'enabled' de abajo.
      return classService.getClassById(classId!);
    },

    // 3. LA MAGIA DE `enabled`: Esta es la opción más importante aquí. Le dice a
    // TanStack Query: "NO ejecutes esta petición a menos que la condición sea
    // verdadera". En este caso, la petición solo se disparará si `classId`
    // tiene un valor (no es null o undefined).
    enabled: !!classId,
  });

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="3xl" scrollBehavior="inside">
      <ModalOverlay bg="blackAlpha.300" backdropFilter="blur(10px)" />
      <ModalContent>
        <ModalHeader>{gymClass?.name || 'Cargando detalles...'}</ModalHeader>
        <ModalCloseButton />
        <ModalBody pb={6}>
          {/* Los booleanos de TanStack Query controlan la UI del modal */}
          {isLoading && <LoadingSpinner />}
          {isError && <ErrorDisplay message="No se pudieron cargar los detalles de la clase." />}
          {gymClass && <ClassDetailView gymClass={gymClass} />}
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};

export default ClassDetailModal;