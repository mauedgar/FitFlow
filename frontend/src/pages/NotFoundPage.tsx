import { Heading, Text, Button } from '@chakra-ui/react';
import { Link } from 'react-router-dom';


const NotFoundPage: React.FC = () => {
  return (
    <>
      <Heading>404</Heading>
      <Text mt={4}>Pagina no encontrada</Text>
      <Button colorPalette="teal" mt={4} asChild><Link to="/">Volver al inicio
                </Link></Button>
    </>
  );
};

export default NotFoundPage;