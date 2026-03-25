import { createBrowserRouter } from 'react-router-dom';
import { HomePage } from '../pages/home/ui/HomePage';
import { ResultPage } from '../pages/result/ui/ResultPage';
import { BanPickPage } from '../pages/banpick/ui/BanPickPage';
import { DesignSystemPage } from '../pages/design-system/ui/DesignSystemPage';

const basename = import.meta.env.BASE_URL || '/';

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
  {
    path: '/design-system',
    element: <DesignSystemPage />,
  },
], {
  basename: basename.endsWith('/') ? basename.slice(0, -1) : basename,
});
