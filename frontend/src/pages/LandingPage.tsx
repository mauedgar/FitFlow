import { Box } from '@chakra-ui/react';
import InfiniteCarousel from '../components/landing/InfiniteCarousel';
import ActivitiesSection from '../components/landing/ActivitiesSection';

const LandingPage = () => {
  return (
    <Box>
      <InfiniteCarousel />
      <ActivitiesSection />
    </Box>
  );
};

export default LandingPage;