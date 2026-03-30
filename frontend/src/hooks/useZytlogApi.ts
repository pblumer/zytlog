import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  clockIn,
  clockOut,
  getCurrentStatus,
  getDailyAccount,
  getEmployees,
  getMonthReport,
  getTimeStamps,
  getWeekReport,
  getWorkingTimeModels,
  getYearReport,
} from '../api/endpoints';
import { useAuth } from '../auth/provider';

export function useCurrentStatus() {
  const { token } = useAuth();
  return useQuery({
    queryKey: ['current-status'],
    queryFn: () => getCurrentStatus(token),
  });
}

export function useDailyAccount(date: string) {
  const { token } = useAuth();
  return useQuery({
    queryKey: ['daily-account', date],
    queryFn: () => getDailyAccount(date, token),
  });
}

export function useTimeStamps(from: string, to: string) {
  const { token } = useAuth();
  return useQuery({
    queryKey: ['time-stamps', from, to],
    queryFn: () => getTimeStamps(from, to, token),
  });
}

export function useWeekReport(year: number, week: number) {
  const { token } = useAuth();
  return useQuery({
    queryKey: ['week-report', year, week],
    queryFn: () => getWeekReport(year, week, token),
  });
}

export function useMonthReport(year: number, month: number) {
  const { token } = useAuth();
  return useQuery({
    queryKey: ['month-report', year, month],
    queryFn: () => getMonthReport(year, month, token),
  });
}

export function useYearReport(year: number) {
  const { token } = useAuth();
  return useQuery({
    queryKey: ['year-report', year],
    queryFn: () => getYearReport(year, token),
  });
}

export function useEmployees(enabled: boolean) {
  const { token } = useAuth();
  return useQuery({
    queryKey: ['employees'],
    queryFn: () => getEmployees(token),
    enabled,
  });
}

export function useWorkingTimeModels(enabled: boolean) {
  const { token } = useAuth();
  return useQuery({
    queryKey: ['working-time-models'],
    queryFn: () => getWorkingTimeModels(token),
    enabled,
  });
}

export function useClockMutation(type: 'in' | 'out') {
  const queryClient = useQueryClient();
  const { token } = useAuth();

  return useMutation({
    mutationFn: () => (type === 'in' ? clockIn(token) : clockOut(token)),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['current-status'] }),
        queryClient.invalidateQueries({ queryKey: ['daily-account'] }),
        queryClient.invalidateQueries({ queryKey: ['time-stamps'] }),
        queryClient.invalidateQueries({ queryKey: ['week-report'] }),
        queryClient.invalidateQueries({ queryKey: ['month-report'] }),
        queryClient.invalidateQueries({ queryKey: ['year-report'] }),
      ]);
    },
  });
}
