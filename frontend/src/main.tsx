import React from 'react';
import ReactDOM from 'react-dom/client';
import { ChakraProvider } from '@chakra-ui/react';
import App from './App';
import { AuthProvider } from './context/AuthProvider'; // Importamos nuestro proveedor

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ChakraProvider>
        <AuthProvider> {/* Envolvemos la App */}
          <App />
        </AuthProvider>      
    </ChakraProvider>
  </React.StrictMode>
);