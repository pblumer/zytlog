import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  clockIn,
  clockOut,
  createEmployee,
  createManualTimeStamp,
  createWorkingTimeModel,
  createHolidaySet,
  commitOpenHolidaysImport,
  createHoliday,
  deleteHolidaySet,
  deleteHoliday,
  createNonWorkingPeriodSet,
  updateNonWorkingPeriodSet,
  deleteNonWorkingPeriodSet,
  createNonWorkingPeriod,
  updateNonWorkingPeriod,
  deleteNonWorkingPeriod,
  deleteWorkingTimeModel,
  deleteTimeStamp,
  getCalendarMonth,
  getCurrentStatus,
  getDailyAccount,
  getEmployees,
  getEmployeeUserOptions,
  getMonthReport,
  getTimeStamps,
  getWeekReport,
  getWorkingTimeModels,
  getHolidays,
  getHolidaySets,
  getNonWorkingPeriodSets,
  getNonWorkingPeriods,
  getOpenHolidaysCountries,
  getOpenHolidaysLanguages,
  getOpenHolidaysSubdivisions,
  updateEmployee,
  updateHoliday,
  updateHolidaySet,
  updateTimeStamp,
  updateWorkingTimeModel,
  previewOpenHolidaysImport,
  getYearReport,
  getMyAbsences,
  createMyAbsence,
  getAdminAbsences,
  createAdminAbsence,
  updateAdminAbsence,
  deleteAdminAbsence,
  getSystemTenants,
  createSystemTenant,
  updateSystemTenant,
  getSystemUsers,
  updateSystemUser,
  type CreateEmployeePayload,
  type CreateHolidayPayload,
  type CreateHolidaySetPayload,
  type CreateWorkingTimeModelPayload,
  type UpdateHolidayPayload,
  type UpdateHolidaySetPayload,
  type UpdateWorkingTimeModelPayload,
  type UpdateEmployeePayload,
  type CreateNonWorkingPeriodSetPayload,
  type UpdateNonWorkingPeriodSetPayload,
  type CreateNonWorkingPeriodPayload,
  type UpdateNonWorkingPeriodPayload,
  type CreateAbsencePayload,
  type UpdateAbsencePayload,
  type OpenHolidaysImportPayload,
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

export function useEmployeeUserOptions(enabled: boolean, withoutEmployeeOnly = true) {
  const { token } = useAuth();
  return useQuery({
    queryKey: ['employee-user-options', withoutEmployeeOnly],
    queryFn: () => getEmployeeUserOptions(withoutEmployeeOnly, token),
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


export function useNonWorkingPeriodSets(enabled: boolean) {
  const { token } = useAuth();
  return useQuery({
    queryKey: ['non-working-period-sets'],
    queryFn: () => getNonWorkingPeriodSets(token),
    enabled,
  });
}

export function useNonWorkingPeriods(periodSetId: number | null, enabled: boolean) {
  const { token } = useAuth();
  return useQuery({
    queryKey: ['non-working-periods', periodSetId],
    queryFn: () => getNonWorkingPeriods(periodSetId ?? -1, token),
    enabled: enabled && periodSetId !== null,
  });
}

export function useCreateNonWorkingPeriodSetMutation() {
  const queryClient = useQueryClient();
  const { token } = useAuth();
  return useMutation({
    mutationFn: (payload: CreateNonWorkingPeriodSetPayload) => createNonWorkingPeriodSet(payload, token),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['non-working-period-sets'] });
    },
  });
}

export function useUpdateNonWorkingPeriodSetMutation() {
  const queryClient = useQueryClient();
  const { token } = useAuth();
  return useMutation({
    mutationFn: ({ periodSetId, payload }: { periodSetId: number; payload: UpdateNonWorkingPeriodSetPayload }) =>
      updateNonWorkingPeriodSet(periodSetId, payload, token),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['non-working-period-sets'] });
    },
  });
}

export function useDeleteNonWorkingPeriodSetMutation() {
  const queryClient = useQueryClient();
  const { token } = useAuth();
  return useMutation({
    mutationFn: (periodSetId: number) => deleteNonWorkingPeriodSet(periodSetId, token),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['non-working-period-sets'] }),
        queryClient.invalidateQueries({ queryKey: ['employees'] }),
      ]);
    },
  });
}

export function useCreateNonWorkingPeriodMutation() {
  const queryClient = useQueryClient();
  const { token } = useAuth();
  return useMutation({
    mutationFn: ({ periodSetId, payload }: { periodSetId: number; payload: CreateNonWorkingPeriodPayload }) =>
      createNonWorkingPeriod(periodSetId, payload, token),
    onSuccess: async (_, vars) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['non-working-periods', vars.periodSetId] }),
        queryClient.invalidateQueries({ queryKey: ['non-working-period-sets'] }),
      ]);
    },
  });
}

export function useUpdateNonWorkingPeriodMutation() {
  const queryClient = useQueryClient();
  const { token } = useAuth();
  return useMutation({
    mutationFn: ({ periodSetId, periodId, payload }: { periodSetId: number; periodId: number; payload: UpdateNonWorkingPeriodPayload }) =>
      updateNonWorkingPeriod(periodSetId, periodId, payload, token),
    onSuccess: async (_, vars) => {
      await queryClient.invalidateQueries({ queryKey: ['non-working-periods', vars.periodSetId] });
    },
  });
}

export function useDeleteNonWorkingPeriodMutation() {
  const queryClient = useQueryClient();
  const { token } = useAuth();
  return useMutation({
    mutationFn: ({ periodSetId, periodId }: { periodSetId: number; periodId: number }) =>
      deleteNonWorkingPeriod(periodSetId, periodId, token),
    onSuccess: async (_, vars) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['non-working-periods', vars.periodSetId] }),
        queryClient.invalidateQueries({ queryKey: ['non-working-period-sets'] }),
      ]);
    },
  });
}

export function useOpenHolidaysCountries(enabled: boolean) {
  const { token } = useAuth();
  return useQuery({
    queryKey: ['openholidays', 'countries'],
    queryFn: () => getOpenHolidaysCountries(token),
    enabled,
  });
}

export function useOpenHolidaysLanguages(enabled: boolean) {
  const { token } = useAuth();
  return useQuery({
    queryKey: ['openholidays', 'languages'],
    queryFn: () => getOpenHolidaysLanguages(token),
    enabled,
  });
}

export function useOpenHolidaysSubdivisions(countryIsoCode: string | null, enabled: boolean) {
  const { token } = useAuth();
  return useQuery({
    queryKey: ['openholidays', 'subdivisions', countryIsoCode],
    queryFn: () => getOpenHolidaysSubdivisions(countryIsoCode ?? '', token),
    enabled: enabled && Boolean(countryIsoCode),
  });
}

export function usePreviewOpenHolidaysImportMutation() {
  const { token } = useAuth();
  return useMutation({
    mutationFn: ({ holidaySetId, payload }: { holidaySetId: number; payload: OpenHolidaysImportPayload }) =>
      previewOpenHolidaysImport(holidaySetId, payload, token),
  });
}

export function useCommitOpenHolidaysImportMutation() {
  const queryClient = useQueryClient();
  const { token } = useAuth();
  return useMutation({
    mutationFn: ({ holidaySetId, payload }: { holidaySetId: number; payload: OpenHolidaysImportPayload }) =>
      commitOpenHolidaysImport(holidaySetId, payload, token),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['holidays'] }),
        queryClient.invalidateQueries({ queryKey: ['holiday-sets'] }),
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
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['employees'] }),
        queryClient.invalidateQueries({ queryKey: ['employee-user-options'] }),
      ]);
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


export function useMyAbsences(from?: string, to?: string) {
  const { token } = useAuth();
  return useQuery({
    queryKey: ['my-absences', from ?? null, to ?? null],
    queryFn: () => getMyAbsences(token, from, to),
  });
}

export function useAdminAbsences(enabled: boolean, employeeId?: number, from?: string, to?: string) {
  const { token } = useAuth();
  return useQuery({
    queryKey: ['admin-absences', employeeId ?? null, from ?? null, to ?? null],
    queryFn: () => getAdminAbsences(token, employeeId, from, to),
    enabled,
  });
}

export function useCreateMyAbsenceMutation() {
  const queryClient = useQueryClient();
  const { token } = useAuth();
  return useMutation({
    mutationFn: (payload: CreateAbsencePayload) => createMyAbsence(payload, token),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['my-absences'] }),
        queryClient.invalidateQueries({ queryKey: ['daily-account'] }),
        queryClient.invalidateQueries({ queryKey: ['month-report'] }),
        queryClient.invalidateQueries({ queryKey: ['week-report'] }),
      ]);
    },
  });
}

export function useCreateAdminAbsenceMutation() {
  const queryClient = useQueryClient();
  const { token } = useAuth();
  return useMutation({
    mutationFn: (payload: CreateAbsencePayload) => createAdminAbsence(payload, token),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['admin-absences'] }),
        queryClient.invalidateQueries({ queryKey: ['my-absences'] }),
        queryClient.invalidateQueries({ queryKey: ['daily-account'] }),
        queryClient.invalidateQueries({ queryKey: ['month-report'] }),
      ]);
    },
  });
}

export function useSystemTenants(enabled: boolean) {
  const { token } = useAuth();
  return useQuery({
    queryKey: ['system-tenants'],
    queryFn: () => getSystemTenants(token),
    enabled,
  });
}

export function useSystemUsers(enabled: boolean) {
  const { token } = useAuth();
  return useQuery({
    queryKey: ['system-users'],
    queryFn: () => getSystemUsers(token),
    enabled,
  });
}

export function useCreateSystemTenantMutation() {
  const queryClient = useQueryClient();
  const { token } = useAuth();
  return useMutation({
    mutationFn: (payload: Parameters<typeof createSystemTenant>[0]) => createSystemTenant(payload, token),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['system-tenants'] });
    },
  });
}

export function useUpdateSystemTenantMutation() {
  const queryClient = useQueryClient();
  const { token } = useAuth();
  return useMutation({
    mutationFn: ({ tenantId, payload }: { tenantId: number; payload: Parameters<typeof updateSystemTenant>[1] }) =>
      updateSystemTenant(tenantId, payload, token),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['system-tenants'] });
    },
  });
}

export function useUpdateSystemUserMutation() {
  const queryClient = useQueryClient();
  const { token } = useAuth();
  return useMutation({
    mutationFn: ({ userId, payload }: { userId: number; payload: Parameters<typeof updateSystemUser>[1] }) =>
      updateSystemUser(userId, payload, token),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['system-users'] }),
        queryClient.invalidateQueries({ queryKey: ['system-tenants'] }),
      ]);
    },
  });
}

export function useUpdateAdminAbsenceMutation() {
  const queryClient = useQueryClient();
  const { token } = useAuth();
  return useMutation({
    mutationFn: ({ absenceId, payload }: { absenceId: number; payload: UpdateAbsencePayload }) =>
      updateAdminAbsence(absenceId, payload, token),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['admin-absences'] });
    },
  });
}

export function useDeleteAdminAbsenceMutation() {
  const queryClient = useQueryClient();
  const { token } = useAuth();
  return useMutation({
    mutationFn: (absenceId: number) => deleteAdminAbsence(absenceId, token),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['admin-absences'] });
    },
  });
}
