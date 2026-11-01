import { Portal, Toast, Toaster as ChakraToaster } from '@chakra-ui/react';
import { toaster } from './toaster-store';

export function Toaster() {
  return (
    <Portal>
      <ChakraToaster toaster={toaster} width="min(400px, calc(100vw - 32px))" maxW="calc(100vw - 32px)">
        {(toast) => (
          <Toast.Root key={toast.id} minW={0} pe="10" overflowWrap="anywhere">
            <Toast.Indicator />
            <Toast.Title minW={0}>{toast.title}</Toast.Title>
            <Toast.Description minW={0}>{toast.description}</Toast.Description>
            {toast.closable && <Toast.CloseTrigger aria-label="Cerrar notificación" />}
          </Toast.Root>
        )}
      </ChakraToaster>
    </Portal>
  );
}
