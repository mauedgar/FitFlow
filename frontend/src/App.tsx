import { BrowserRouter} from 'react-router-dom';
import { AppRouter } from './routes/AppRouter.tsx';

const App: React.FC = () => {
  return (
      <BrowserRouter future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true 
      }}>        
        <AppRouter/>
      </BrowserRouter>
  );
}

export default App;

