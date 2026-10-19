import { Navigate } from 'react-router-dom';
import { RequireAuth } from '@/components/RequireAuth';
import { AdminLayout } from '@/layout/AdminLayout';
import { LoginPage } from '@/pages/login/index.jsx';
import { NotFound } from '@/pages/notFound/index.jsx';
import { appRoutesConfig } from '@/routes/config.js';

export const appRoutes = [
  { path: '/', element: <Navigate to="/login" replace /> },
  { path: '/login', element: <LoginPage /> },
  {
    element: <RequireAuth />,
    children: [
      {
        element: <AdminLayout />,
        children: appRoutesConfig.flatMap((group) =>
          group.children.map((child) => {
            const Component = child.component;
            return {
              path: `${group.path}/${child.path}`,
              element: <Component />,
            };
          }),
        ),
      },
    ],
  },
  { path: '*', element: <NotFound /> },
];
