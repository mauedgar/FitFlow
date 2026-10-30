import React from 'react';
import ReactDOM from 'react-dom/client';
import { ChakraProvider, defaultSystem } from '@chakra-ui/react';
import App from './App';
import { AuthProvider } from './context/AuthProvider'; // Importamos nuestro proveedor
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'; // Importa
import { Toaster } from './components/ui/toaster';

const queryClient = new QueryClient();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ChakraProvider value={defaultSystem}>
          <AuthProvider> {/* Envolvemos la App */}
            <App />
            <Toaster />
          </AuthProvider>
      </ChakraProvider>
    </QueryClientProvider>
  </React.StrictMode>
);
