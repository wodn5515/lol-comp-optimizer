import { createBrowserRouter } from 'react-router-dom';
import { HomePage } from '../pages/home/ui/HomePage';
import { ResultPage } from '../pages/result/ui/ResultPage';
import { BanPickPage } from '../pages/banpick/ui/BanPickPage';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <HomePage />,
  },
  {
    path: '/banpick',
    element: <BanPickPage />,
  },
  {
    path: '/result',
    element: <ResultPage />,
  },
]);
