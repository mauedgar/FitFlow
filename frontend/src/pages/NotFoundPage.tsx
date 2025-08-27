import { Heading, Text, Button } from '@chakra-ui/react';
import { Link } from 'react-router-dom';


const NotFoundPage: React.FC = () => {
  return (
    <>
      <Heading>404</Heading>
      <Text mt={4}>Pagina no encontrada</Text>
      <Button as={Link} to="/" colorScheme="teal" mt={4}>
         Volver al inicio
        </Button>
    </>
  );
};

export default NotFoundPage;