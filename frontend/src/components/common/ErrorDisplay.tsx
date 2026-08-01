// src/components/common/ErrorDisplay.tsx (Modificado)
import React from 'react';
import { Alert, AlertIcon, AlertTitle, AlertDescription, VStack, Text, HStack } from '@chakra-ui/react';
import { AxiosError } from 'axios'; // Asegúrate de importar AxiosError
import { type FastAPIValidationError } from '../../types'; // O donde la definas

interface ErrorDisplayProps {
  // Ahora acepta el objeto de error real para extraer más detalles
  error?: unknown;
  message?: string; // Mensaje genérico de fallback si no se puede parsear el error
}

const ErrorDisplay: React.FC<ErrorDisplayProps> = ({ error, message }) => {
  let displayTitle = '¡Ocurrió un error!';
  let displayMessage = message || 'Ha sucedido un problema inesperado.';
  let detailMessage: string | null = null;
  let statusCode: number | null = null;

  if (error instanceof AxiosError) {
    statusCode = error.response?.status || null;
    displayTitle = `Error de la API (Código: ${statusCode || 'Desconocido'})`;

    if (error.response?.data) {
      // Intenta obtener el detalle del error de FastAPI
      const errorData = error.response.data;
      if (typeof errorData === 'object' && errorData !== null) {
        if ('detail' in errorData) {
          if (typeof errorData.detail === 'string') {
            detailMessage = errorData.detail;
          } else if (Array.isArray(errorData.detail)) {
            // FastAPI a veces devuelve un array de errores de validación
            detailMessage = errorData.detail.map((err: FastAPIValidationError) => 
              `${err.loc.join('.')} - ${err.msg}`
            ).join('; ');
          } else {
            detailMessage = JSON.stringify(errorData.detail); // Para otros formatos de detail
          }
        } else if ('message' in errorData) { // Algunas APIs usan 'message' en lugar de 'detail'
          detailMessage = String(errorData.message);
        } else {
          detailMessage = JSON.stringify(errorData); // Fallback para mostrar todo el objeto
        }
      } else if (typeof errorData === 'string') {
        detailMessage = errorData;
      }
    } else if (error.request) {
      displayMessage = "No se recibió respuesta del servidor. Podría ser un problema de red o que el servidor no está corriendo.";
    } else {
      displayMessage = `Error al configurar la petición: ${error.message}`;
    }
  } else if (error instanceof Error) {
    displayTitle = 'Error interno del cliente';
    displayMessage = error.message;
  }

  // Si no se pudo obtener un detalle específico, usar el mensaje genérico
  if (!detailMessage && message) {
    detailMessage = message;
  }
  // Si sigue sin haber detalle, usar el mensaje de Axios si está disponible
  if (!detailMessage && error instanceof AxiosError && error.message) {
    detailMessage = error.message;
  }


  return (
    <Alert status="error" variant="left-accent" flexDirection="column" alignItems="flex-start" justifyContent="center" textAlign="left" py={4} rounded="md" shadow="md">
      <HStack>
        <AlertIcon />
        <AlertTitle mr={0}>{displayTitle}</AlertTitle>
      </HStack>
      <AlertDescription mt={2}>
        <VStack align="flex-start" spacing={1}>
          {displayMessage && <Text>{displayMessage}</Text>}
          {detailMessage && <Text fontSize="sm" color="gray.600">Detalle: {detailMessage}</Text>}
        </VStack>
      </AlertDescription>
    </Alert>
  );
};

export default ErrorDisplay;