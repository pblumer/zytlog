import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  clockIn,
  clockOut,
  createEmployee,
  createManualTimeStamp,
  createWorkingTimeModel,
  createHolidaySet,
  createHoliday,
  deleteHolidaySet,
  deleteHoliday,
  deleteWorkingTimeModel,
  deleteTimeStamp,
  getCalendarMonth,
  getCurrentStatus,
  getDailyAccount,
  getEmployees,
  getMonthReport,
  getTimeStamps,
  getWeekReport,
  getWorkingTimeModels,
  getHolidays,
  getHolidaySets,
  updateEmployee,
  updateHoliday,
  updateHolidaySet,
  updateTimeStamp,
  updateWorkingTimeModel,
  getYearReport,
  type CreateEmployeePayload,
  type CreateHolidayPayload,
  type CreateHolidaySetPayload,
  type CreateWorkingTimeModelPayload,
  type UpdateHolidayPayload,
  type UpdateHolidaySetPayload,
  type UpdateWorkingTimeModelPayload,
  type UpdateEmployeePayload,
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

export function useDashboardCalendarMonth(year: number, month: number) {
  const { token } = useAuth();
  return useQuery({
    queryKey: ['dashboard-calendar', year, month],
    queryFn: () => getCalendarMonth(year, month, token),
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


export function useHolidays(enabled: boolean, year?: number, holidaySetId?: number) {
  const { token } = useAuth();
  return useQuery({
    queryKey: ['holidays', year ?? null, holidaySetId ?? null],
    queryFn: () => getHolidays(token, year, holidaySetId),
    enabled,
  });
}
export function useHolidaySets(enabled: boolean) {
  const { token } = useAuth();
  return useQuery({
    queryKey: ['holiday-sets'],
    queryFn: () => getHolidaySets(token),
    enabled,
  });
}

export function useCreateHolidayMutation() {
  const queryClient = useQueryClient();
  const { token } = useAuth();
  return useMutation({
    mutationFn: (payload: CreateHolidayPayload) => createHoliday(payload, token),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['holidays'] });
    },
  });
}

export function useUpdateHolidayMutation() {
  const queryClient = useQueryClient();
  const { token } = useAuth();
  return useMutation({
    mutationFn: ({ holidayId, payload }: { holidayId: number; payload: UpdateHolidayPayload }) =>
      updateHoliday(holidayId, payload, token),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['holidays'] });
    },
  });
}

export function useDeleteHolidayMutation() {
  const queryClient = useQueryClient();
  const { token } = useAuth();
  return useMutation({
    mutationFn: (holidayId: number) => deleteHoliday(holidayId, token),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['holidays'] });
    },
  });
}

export function useCreateHolidaySetMutation() {
  const queryClient = useQueryClient();
  const { token } = useAuth();
  return useMutation({
    mutationFn: (payload: CreateHolidaySetPayload) => createHolidaySet(payload, token),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['holiday-sets'] });
    },
  });
}

export function useUpdateHolidaySetMutation() {
  const queryClient = useQueryClient();
  const { token } = useAuth();
  return useMutation({
    mutationFn: ({ holidaySetId, payload }: { holidaySetId: number; payload: UpdateHolidaySetPayload }) =>
      updateHolidaySet(holidaySetId, payload, token),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['holiday-sets'] });
    },
  });
}

export function useDeleteHolidaySetMutation() {
  const queryClient = useQueryClient();
  const { token } = useAuth();
  return useMutation({
    mutationFn: (holidaySetId: number) => deleteHolidaySet(holidaySetId, token),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['holiday-sets'] }),
        queryClient.invalidateQueries({ queryKey: ['holidays'] }),
      ]);
    },
  });
}
export function useCreateWorkingTimeModelMutation() {
  const queryClient = useQueryClient();
  const { token } = useAuth();
  return useMutation({
    mutationFn: (payload: CreateWorkingTimeModelPayload) => createWorkingTimeModel(payload, token),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['working-time-models'] });
    },
  });
}

export function useUpdateWorkingTimeModelMutation() {
  const queryClient = useQueryClient();
  const { token } = useAuth();
  return useMutation({
    mutationFn: ({ modelId, payload }: { modelId: number; payload: UpdateWorkingTimeModelPayload }) =>
      updateWorkingTimeModel(modelId, payload, token),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['working-time-models'] });
    },
  });
}

export function useDeleteWorkingTimeModelMutation() {
  const queryClient = useQueryClient();
  const { token } = useAuth();
  return useMutation({
    mutationFn: (modelId: number) => deleteWorkingTimeModel(modelId, token),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['working-time-models'] });
    },
  });
}

export function useCreateEmployeeMutation() {
  const queryClient = useQueryClient();
  const { token } = useAuth();
  return useMutation({
    mutationFn: (payload: CreateEmployeePayload) => createEmployee(payload, token),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['employees'] });
    },
  });
}

export function useUpdateEmployeeMutation() {
  const queryClient = useQueryClient();
  const { token } = useAuth();
  return useMutation({
    mutationFn: ({ employeeId, payload }: { employeeId: number; payload: UpdateEmployeePayload }) =>
      updateEmployee(employeeId, payload, token),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['employees'] });
    },
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
        queryClient.invalidateQueries({ queryKey: ['dashboard-calendar'] }),
      ]);
    },
  });
}

export function useUpdateTimeStampMutation() {
  const queryClient = useQueryClient();
  const { token } = useAuth();

  return useMutation({
    mutationFn: ({ eventId, timestamp, comment }: { eventId: number; timestamp: string; comment: string | null }) =>
      updateTimeStamp(eventId, { timestamp, comment }, token),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['current-status'] }),
        queryClient.invalidateQueries({ queryKey: ['time-stamps'] }),
        queryClient.invalidateQueries({ queryKey: ['daily-account'] }),
        queryClient.invalidateQueries({ queryKey: ['week-report'] }),
        queryClient.invalidateQueries({ queryKey: ['month-report'] }),
        queryClient.invalidateQueries({ queryKey: ['year-report'] }),
        queryClient.invalidateQueries({ queryKey: ['dashboard-calendar'] }),
      ]);
    },
  });
}

export function useManualTimeStampMutation() {
  const queryClient = useQueryClient();
  const { token } = useAuth();

  return useMutation({
    mutationFn: ({ timestamp, type, comment }: { timestamp: string; type: 'clock_in' | 'clock_out'; comment: string | null }) =>
      createManualTimeStamp({ timestamp, type, comment }, token),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['current-status'] }),
        queryClient.invalidateQueries({ queryKey: ['time-stamps'] }),
        queryClient.invalidateQueries({ queryKey: ['daily-account'] }),
        queryClient.invalidateQueries({ queryKey: ['week-report'] }),
        queryClient.invalidateQueries({ queryKey: ['month-report'] }),
        queryClient.invalidateQueries({ queryKey: ['year-report'] }),
        queryClient.invalidateQueries({ queryKey: ['dashboard-calendar'] }),
      ]);
    },
  });
}

export function useDeleteTimeStampMutation() {
  const queryClient = useQueryClient();
  const { token } = useAuth();

  return useMutation({
    mutationFn: (eventId: number) => deleteTimeStamp(eventId, token),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['current-status'] }),
        queryClient.invalidateQueries({ queryKey: ['time-stamps'] }),
        queryClient.invalidateQueries({ queryKey: ['daily-account'] }),
        queryClient.invalidateQueries({ queryKey: ['week-report'] }),
        queryClient.invalidateQueries({ queryKey: ['month-report'] }),
        queryClient.invalidateQueries({ queryKey: ['year-report'] }),
        queryClient.invalidateQueries({ queryKey: ['dashboard-calendar'] }),
      ]);
    },
  });
}
