import { useState, useEffect } from 'react';
import { Box, Button, Flex, Heading, Text, VStack, HStack } from '@chakra-ui/react';
import { Link as RouterLink } from 'react-router-dom';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';

// Los mismos datos que ya teníamos
const carouselSlides = [
    {
        image: 'https://images.unsplash.com/photo-1571902943202-507ec2618e8f?ixlib=rb-4.0.3&q=85&fm=jpg&crop=entropy&cs=srgb&w=1600',
        title: 'Planes a Tu Medida',
        subtitle: 'Encuentra la membresía perfecta para alcanzar tus objetivos.',
        buttonText: 'Ver Planes',
        link: '/plans',
    },
    {
        image: 'https://images.unsplash.com/photo-1540496905036-5937c3624e5s?ixlib=rb-4.0.3&q=85&fm=jpg&crop=entropy&cs=srgb&w=1600',
        title: 'Clases y Horarios Flexibles',
        subtitle: 'Yoga, Spinning, CrossFit y más. Encuentra tu clase ideal.',
        buttonText: 'Ver Horarios',
        link: '/classes',
    },
    {
        image: 'https://images.unsplash.com/photo-1522071820081-009f0129c71c?ixlib=rb-4.0.3&q=85&fm=jpg&crop=entropy&cs=srgb&w=1600',
        title: 'Súmate a Nuestro Equipo',
        subtitle: 'Buscamos personas apasionadas por el fitness para crecer juntos.',
        buttonText: 'Únete Ahora',
        link: '/join-us',
    },
    {
        image: 'https://images.unsplash.com/photo-1498837167922-ddd27525d352?ixlib=rb-4.0.3&q=85&fm=jpg&crop=entropy&cs=srgb&w=1600',
        title: 'Nutrición Inteligente',
        subtitle: 'Asesoramiento para complementar tu entrenamiento con la mejor alimentación.',
        buttonText: 'Organiza tu Alimentación',
        link: '/nutrition',
    }
];

// 1. Definimos las variantes de animación para la transición
const slideVariants = {
  enter: {
    opacity: 0,
    x: '100vw',
  },
  center: {
    zIndex: 1,
    opacity: 1,
    x: 0,
  },
  exit: {
    zIndex: 0,
    opacity: 0,
    x: '-100vw',
  },
};

const InfiniteCarousel = () => {
  // 2. Estado para saber qué diapositiva está activa
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const shouldReduceMotion = useReducedMotion();

  // 3. useEffect para el cambio automático de diapositiva
  useEffect(() => {
    if (isPaused || shouldReduceMotion) return;

    const slideInterval = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % carouselSlides.length);
    }, 6000);

    return () => clearInterval(slideInterval);
  }, [isPaused, shouldReduceMotion]);

  // Función para cambiar de diapositiva manualmente
  const goToSlide = (slideIndex: number) => {
    setCurrentSlide(slideIndex);
  };

  return (
    <Box
      position="relative"
      width="full"
      height="calc(100vh - 64px)"
      overflow="hidden"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
      onFocusCapture={() => setIsPaused(true)}
      onBlurCapture={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
          setIsPaused(false);
        }
      }}
    >
      {/* 4. AnimatePresence es la clave para animar la salida de un componente */}
      <AnimatePresence initial={false} mode="wait">
        <motion.div
          key={currentSlide} // La key es crucial para que AnimatePresence detecte el cambio
          variants={slideVariants}
          initial={shouldReduceMotion ? false : "enter"}
          animate="center"
          exit="exit"
          transition={shouldReduceMotion ? { duration: 0 } : {
            x: { type: 'spring', stiffness: 300, damping: 30 },
            opacity: { duration: 0.3 },
          }}
          style={{
            position: 'absolute',
            width: '100%',
            height: '100%',
          }}
        >
          <Flex
            width="100%"
            height="100%"
            align="center"
            justify="center"
            backgroundImage={`url(${carouselSlides[currentSlide].image})`}
            backgroundPosition="center"
            backgroundSize="cover"
          >
            <Box position="absolute" top="0" left="0" right="0" bottom="0" bg="blackAlpha.600" />
            <VStack
              justify="center"
              align="center"
              color="white"
              textAlign="center"
              gap={6}
              position="relative"
              px={4}
              zIndex={2}
            >
              <Heading as="h1" size={{ base: '2xl', md: '4xl' }} textShadow="2px 2px 4px rgba(0,0,0,0.5)">
                {carouselSlides[currentSlide].title}
              </Heading>
              <Text fontSize={{ base: 'lg', md: '2xl' }} maxWidth="700px" textShadow="1px 1px 3px rgba(0,0,0,0.5)">
                {carouselSlides[currentSlide].subtitle}
              </Text>
              <Button colorPalette="teal" size="lg" mt={4} asChild><RouterLink to={carouselSlides[currentSlide].link}>
                  {carouselSlides[currentSlide].buttonText}
                </RouterLink></Button>
            </VStack>
          </Flex>
        </motion.div>
      </AnimatePresence>

      {/* 5. La "barra de desplazamiento" (puntos de navegación) */}
      <HStack
        justify="center"
        gap={4}
        position="absolute"
        bottom="40px"
        width="full"
        zIndex={3}
      >
        {carouselSlides.map((slide, index) => (
          <Box
            key={slide.link}
            // El punto activo es más ancho
            width={currentSlide === index ? '24px' : '12px'}
            height="12px"
            borderRadius="full"
            bg={currentSlide === index ? 'teal.400' : 'whiteAlpha.600'}
            transition="all 0.3s ease-in-out"
            asChild><button type="button" aria-label={`Ir a la diapositiva ${index + 1}: ${slide.title}`} aria-current={currentSlide === index ? 'true' : undefined} onClick={() => goToSlide(index)} /></Box>
        ))}
      </HStack>
    </Box>
  );
};

export default InfiniteCarousel;
