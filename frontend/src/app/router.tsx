import { createBrowserRouter } from 'react-router-dom';

import { ProtectedRoute } from './ProtectedRoute';
import { AppShell } from '../layout/AppShell';
import { AdminAbsencesPage } from '../pages/AdminAbsencesPage';
import { DashboardPage } from '../pages/DashboardPage';
import { DayPage } from '../pages/DayPage';
import { EmployeesPage } from '../pages/EmployeesPage';
import { HolidaySetsPage } from '../pages/HolidaySetsPage';
import { HolidaysPage } from '../pages/HolidaysPage';
import { MonthPage } from '../pages/MonthPage';
import { MyAbsencesPage } from '../pages/MyAbsencesPage';
import { MyTimePage } from '../pages/MyTimePage';
import { NonWorkingPeriodSetsPage } from '../pages/NonWorkingPeriodSetsPage';
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
          { path: 'my-absences', element: <MyAbsencesPage /> },
          { path: 'employees', element: <EmployeesPage /> },
          { path: 'working-time-models', element: <WorkingTimeModelsPage /> },
          { path: 'holiday-sets', element: <HolidaySetsPage /> },
          { path: 'holidays', element: <HolidaysPage /> },
          { path: 'non-working-period-sets', element: <NonWorkingPeriodSetsPage /> },
          { path: 'admin-absences', element: <AdminAbsencesPage /> },
          { path: '*', element: <NotFoundPage /> },
        ],
      },
    ],
  },
]);
