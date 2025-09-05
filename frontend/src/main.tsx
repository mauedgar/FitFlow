import React from 'react';
import ReactDOM from 'react-dom/client';
import { ChakraProvider } from '@chakra-ui/react';
import App from './App';
import { AuthProvider } from './context/AuthProvider'; // Importamos nuestro proveedor
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'; // Importa

const queryClient = new QueryClient();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>

      <ChakraProvider>
          <AuthProvider> {/* Envolvemos la App */}
            <App />
          </AuthProvider>      
      </ChakraProvider>
    </QueryClientProvider>
  </React.StrictMode>
);