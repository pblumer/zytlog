import { createBrowserRouter } from 'react-router-dom';

import { ProtectedRoute } from './ProtectedRoute';
import { AppShell } from '../layout/AppShell';
import { DashboardPage } from '../pages/DashboardPage';
import { DayPage } from '../pages/DayPage';
import { EmployeesPage } from '../pages/EmployeesPage';
import { HolidaysPage } from '../pages/HolidaysPage';
import { MonthPage } from '../pages/MonthPage';
import { MyTimePage } from '../pages/MyTimePage';
import { NotFoundPage } from '../pages/NotFoundPage';
import { UnauthorizedPage } from '../pages/UnauthorizedPage';
import { WeekPage } from '../pages/WeekPage';
import { WorkingTimeModelsPage } from '../pages/WorkingTimeModelsPage';
import { YearPage } from '../pages/YearPage';

export const router = createBrowserRouter([
  { path: '/unauthorized', element: <UnauthorizedPage /> },
  {
    element: <ProtectedRoute />,
    children: [
      {
        path: '/',
        element: <AppShell />,
        children: [
          { index: true, element: <DashboardPage /> },
          { path: 'my-time', element: <MyTimePage /> },
          { path: 'day', element: <DayPage /> },
          { path: 'week', element: <WeekPage /> },
          { path: 'month', element: <MonthPage /> },
          { path: 'year', element: <YearPage /> },
          { path: 'employees', element: <EmployeesPage /> },
          { path: 'working-time-models', element: <WorkingTimeModelsPage /> },
          { path: 'holidays', element: <HolidaysPage /> },
          { path: '*', element: <NotFoundPage /> },
        ],
      },
    ],
  },
]);
