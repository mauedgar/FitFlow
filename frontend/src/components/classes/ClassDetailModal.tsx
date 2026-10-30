import React from 'react';
import { CloseButton, Dialog, Portal } from '@chakra-ui/react';
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
  const { data: gymClass, isLoading, isError, error } = useQuery({
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
    <Dialog.Root open={isOpen} size='xl' scrollBehavior="inside" onOpenChange={e => {
      if (!e.open) {
        onClose();
      }
    }}>
      <Portal>

        <Dialog.Backdrop bg="blackAlpha.300" backdropFilter="blur(10px)" />
        <Dialog.Positioner>
          <Dialog.Content>
            <Dialog.Header><Dialog.Title>{gymClass?.name || 'Cargando detalles...'}</Dialog.Title></Dialog.Header>
            <Dialog.CloseTrigger asChild>
              <CloseButton aria-label="Cerrar detalles de la clase" size="sm" position="absolute" top="2" right="2" />
            </Dialog.CloseTrigger>
            <Dialog.Body pb={6}>
              {/* Los booleanos de TanStack Query controlan la UI del modal */}
              {isLoading && <LoadingSpinner />}
              {isError && <ErrorDisplay message={error?.message || "No se pudieron cargar los detalles de la clase."} />}
              {gymClass && <ClassDetailView gymClass={gymClass} onCloseModal={onClose} />} {/* PASAMOS onCloseModal */}
            </Dialog.Body>
          </Dialog.Content>
        </Dialog.Positioner>

      </Portal>
    </Dialog.Root>
  );
};

export default ClassDetailModal;
