import { apiDelete, apiDownload, apiGet, apiPatch, apiPost } from './client';
import type {
  CurrentClockStatus,
  CalendarMonth,
  DailyTimeAccount,
  Employee,
  Me,
  MonthlyOverview,
  TimeStampEvent,
  WeeklyOverview,
  WorkingTimeModel,
  YearlyOverview,
  Holiday,
  HolidaySet,
  Absence,
  OpenHolidaysCountry,
  OpenHolidaysImportCommitResult,
  OpenHolidaysImportPayload,
  OpenHolidaysImportPreview,
  OpenHolidaysLanguage,
  OpenHolidaysSubdivision,
  NonWorkingPeriodSet,
  NonWorkingPeriod,
} from '../types/api';

export type { OpenHolidaysImportPayload } from '../types/api';

export const getMe = (token?: string | null) => apiGet<Me>('/me', token);

export const getCurrentStatus = (token?: string | null) =>
  apiGet<CurrentClockStatus>('/time-stamps/my/current-status', token);

export const getDailyAccount = (date: string, token?: string | null) =>
  apiGet<DailyTimeAccount>(`/daily-accounts/my?date=${encodeURIComponent(date)}`, token);

export const getTimeStamps = (from: string, to: string, token?: string | null) =>
  apiGet<TimeStampEvent[]>(`/time-stamps/my?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`, token);

export const getWeekReport = (year: number, week: number, token?: string | null) =>
  apiGet<WeeklyOverview>(`/reports/my/week?year=${year}&week=${week}`, token);

export const getMonthReport = (year: number, month: number, token?: string | null) =>
  apiGet<MonthlyOverview>(`/reports/my/month?year=${year}&month=${month}`, token);

export const getYearReport = (year: number, token?: string | null) =>
  apiGet<YearlyOverview>(`/reports/my/year?year=${year}`, token);

export const getCalendarMonth = (year: number, month: number, token?: string | null) =>
  apiGet<CalendarMonth>(`/calendar/my/month?year=${year}&month=${month}`, token);

export const downloadDayExport = (date: string, format: 'csv' | 'pdf', token?: string | null) =>
  apiDownload(`/exports/my/day${format === 'pdf' ? '/pdf' : ''}?date=${encodeURIComponent(date)}`, token);

export const downloadWeekExport = (year: number, week: number, format: 'csv' | 'pdf', token?: string | null) =>
  apiDownload(`/exports/my/week${format === 'pdf' ? '/pdf' : ''}?year=${year}&week=${week}`, token);

export const downloadMonthExport = (year: number, month: number, format: 'csv' | 'pdf', token?: string | null) =>
  apiDownload(`/exports/my/month${format === 'pdf' ? '/pdf' : ''}?year=${year}&month=${month}`, token);

export const downloadYearExport = (year: number, format: 'csv' | 'pdf', token?: string | null) =>
  apiDownload(`/exports/my/year${format === 'pdf' ? '/pdf' : ''}?year=${year}`, token);

export const getEmployees = (token?: string | null) => apiGet<Employee[]>('/employees', token);
export type CreateEmployeePayload = {
  user_id: number;
  employee_number: string | null;
  first_name: string;
  last_name: string;
  employment_percentage: number;
  entry_date: string;
  exit_date: string | null;
  working_time_model_id: number | null;
  holiday_set_id: number | null;
  non_working_period_set_id: number | null;
  workday_monday: boolean | null;
  workday_tuesday: boolean | null;
  workday_wednesday: boolean | null;
  workday_thursday: boolean | null;
  workday_friday: boolean | null;
  workday_saturday: boolean | null;
  workday_sunday: boolean | null;
  team: string | null;
};
export const createEmployee = (payload: CreateEmployeePayload, token?: string | null) =>
  apiPost<Employee>('/employees', payload, token);
export type UpdateEmployeePayload = Partial<Omit<CreateEmployeePayload, 'user_id'>>;
export const updateEmployee = (employeeId: number, payload: UpdateEmployeePayload, token?: string | null) =>
  apiPatch<Employee>(`/employees/${employeeId}`, payload, token);

export const getWorkingTimeModels = (token?: string | null) => apiGet<WorkingTimeModel[]>('/working-time-models', token);
export type CreateWorkingTimeModelPayload = {
  name: string;
  annual_target_hours: number;
  default_workday_monday: boolean;
  default_workday_tuesday: boolean;
  default_workday_wednesday: boolean;
  default_workday_thursday: boolean;
  default_workday_friday: boolean;
  default_workday_saturday: boolean;
  default_workday_sunday: boolean;
  active: boolean;
};
export const createWorkingTimeModel = (payload: CreateWorkingTimeModelPayload, token?: string | null) =>
  apiPost<WorkingTimeModel>('/working-time-models', payload, token);
export type UpdateWorkingTimeModelPayload = Partial<CreateWorkingTimeModelPayload>;
export const updateWorkingTimeModel = (modelId: number, payload: UpdateWorkingTimeModelPayload, token?: string | null) =>
  apiPatch<WorkingTimeModel>(`/working-time-models/${modelId}`, payload, token);
export const deleteWorkingTimeModel = (modelId: number, token?: string | null) =>
  apiDelete<void>(`/working-time-models/${modelId}`, token);


export const getHolidays = (token?: string | null, year?: number, holidaySetId?: number) =>
  apiGet<Holiday[]>(
    `/holidays?${new URLSearchParams({
      ...(year ? { year: String(year) } : {}),
      ...(holidaySetId ? { holiday_set_id: String(holidaySetId) } : {}),
    }).toString()}`,
    token,
  );

export type CreateHolidayPayload = {
  holiday_set_id: number;
  date: string;
  name: string;
  active: boolean;
};

export type UpdateHolidayPayload = Partial<CreateHolidayPayload>;

export const createHoliday = (payload: CreateHolidayPayload, token?: string | null) =>
  apiPost<Holiday>('/holidays', payload, token);

export const updateHoliday = (holidayId: number, payload: UpdateHolidayPayload, token?: string | null) =>
  apiPatch<Holiday>(`/holidays/${holidayId}`, payload, token);

export const deleteHoliday = (holidayId: number, token?: string | null) =>
  apiDelete<void>(`/holidays/${holidayId}`, token);

export const getHolidaySets = (token?: string | null) => apiGet<HolidaySet[]>('/holiday-sets', token);

export type CreateHolidaySetPayload = {
  name: string;
  description: string | null;
  source: string | null;
  country_code: string | null;
  region_code: string | null;
  active: boolean;
};
export type UpdateHolidaySetPayload = Partial<CreateHolidaySetPayload>;

export const createHolidaySet = (payload: CreateHolidaySetPayload, token?: string | null) =>
  apiPost<HolidaySet>('/holiday-sets', payload, token);
export const updateHolidaySet = (holidaySetId: number, payload: UpdateHolidaySetPayload, token?: string | null) =>
  apiPatch<HolidaySet>(`/holiday-sets/${holidaySetId}`, payload, token);
export const deleteHolidaySet = (holidaySetId: number, token?: string | null) =>
  apiDelete<void>(`/holiday-sets/${holidaySetId}`, token);


export const getNonWorkingPeriodSets = (token?: string | null) =>
  apiGet<NonWorkingPeriodSet[]>('/non-working-period-sets', token);

export type CreateNonWorkingPeriodSetPayload = {
  name: string;
  description: string | null;
  active: boolean;
};
export type UpdateNonWorkingPeriodSetPayload = Partial<CreateNonWorkingPeriodSetPayload>;

export const createNonWorkingPeriodSet = (payload: CreateNonWorkingPeriodSetPayload, token?: string | null) =>
  apiPost<NonWorkingPeriodSet>('/non-working-period-sets', payload, token);

export const updateNonWorkingPeriodSet = (
  periodSetId: number,
  payload: UpdateNonWorkingPeriodSetPayload,
  token?: string | null,
) => apiPatch<NonWorkingPeriodSet>(`/non-working-period-sets/${periodSetId}`, payload, token);

export const deleteNonWorkingPeriodSet = (periodSetId: number, token?: string | null) =>
  apiDelete<void>(`/non-working-period-sets/${periodSetId}`, token);

export const getNonWorkingPeriods = (periodSetId: number, token?: string | null) =>
  apiGet<NonWorkingPeriod[]>(`/non-working-period-sets/${periodSetId}/periods`, token);

export type CreateNonWorkingPeriodPayload = {
  start_date: string;
  end_date: string;
  name: string;
  category: string | null;
};
export type UpdateNonWorkingPeriodPayload = Partial<CreateNonWorkingPeriodPayload>;

export const createNonWorkingPeriod = (
  periodSetId: number,
  payload: CreateNonWorkingPeriodPayload,
  token?: string | null,
) => apiPost<NonWorkingPeriod>(`/non-working-period-sets/${periodSetId}/periods`, payload, token);

export const updateNonWorkingPeriod = (
  periodSetId: number,
  periodId: number,
  payload: UpdateNonWorkingPeriodPayload,
  token?: string | null,
) => apiPatch<NonWorkingPeriod>(`/non-working-period-sets/${periodSetId}/periods/${periodId}`, payload, token);

export const deleteNonWorkingPeriod = (periodSetId: number, periodId: number, token?: string | null) =>
  apiDelete<void>(`/non-working-period-sets/${periodSetId}/periods/${periodId}`, token);

export const getOpenHolidaysCountries = (token?: string | null) =>
  apiGet<OpenHolidaysCountry[]>('/admin/openholidays/countries', token);

export const getOpenHolidaysLanguages = (token?: string | null) =>
  apiGet<OpenHolidaysLanguage[]>('/admin/openholidays/languages', token);

export const getOpenHolidaysSubdivisions = (countryIsoCode: string, token?: string | null) =>
  apiGet<OpenHolidaysSubdivision[]>(
    `/admin/openholidays/subdivisions?countryIsoCode=${encodeURIComponent(countryIsoCode)}`,
    token,
  );

export const previewOpenHolidaysImport = (
  holidaySetId: number,
  payload: OpenHolidaysImportPayload,
  token?: string | null,
) =>
  apiPost<OpenHolidaysImportPreview>(
    `/admin/holiday-sets/${holidaySetId}/import/openholidays/preview`,
    payload,
    token,
  );

export const commitOpenHolidaysImport = (
  holidaySetId: number,
  payload: OpenHolidaysImportPayload,
  token?: string | null,
) =>
  apiPost<OpenHolidaysImportCommitResult>(
    `/admin/holiday-sets/${holidaySetId}/import/openholidays/commit`,
    payload,
    token,
  );

export const clockIn = (token?: string | null) => apiPost<TimeStampEvent>('/time-stamps/clock-in', undefined, token);

export const clockOut = (token?: string | null) => apiPost<TimeStampEvent>('/time-stamps/clock-out', undefined, token);

export type ManualTimeStampPayload = {
  timestamp: string;
  type: 'clock_in' | 'clock_out';
  comment: string | null;
};

export const createManualTimeStamp = (payload: ManualTimeStampPayload, token?: string | null) =>
  apiPost<TimeStampEvent>('/time-stamps/manual', payload, token);

export type UpdateTimeStampPayload = {
  timestamp: string;
  comment: string | null;
};

export const updateTimeStamp = (eventId: number, payload: UpdateTimeStampPayload, token?: string | null) =>
  apiPatch<TimeStampEvent>(`/time-stamps/${eventId}`, payload, token);

export const deleteTimeStamp = (eventId: number, token?: string | null) =>
  apiDelete<TimeStampEvent>(`/time-stamps/${eventId}`, token);

export type CreateAbsencePayload = {
  employee_id?: number;
  absence_type: 'vacation' | 'sickness';
  start_date: string;
  end_date: string;
  duration_type: 'full_day' | 'half_day_am' | 'half_day_pm';
  note: string | null;
};

export type UpdateAbsencePayload = Partial<CreateAbsencePayload>;

export const getMyAbsences = (token?: string | null, from?: string, to?: string) =>
  apiGet<Absence[]>(`/absences/my?${new URLSearchParams({ ...(from ? { from } : {}), ...(to ? { to } : {}) }).toString()}`, token);

export const createMyAbsence = (payload: CreateAbsencePayload, token?: string | null) =>
  apiPost<Absence>('/absences/my', payload, token);

export const getAdminAbsences = (
  token?: string | null,
  employeeId?: number,
  from?: string,
  to?: string,
) =>
  apiGet<Absence[]>(
    `/admin/absences?${new URLSearchParams({
      ...(employeeId ? { employee_id: String(employeeId) } : {}),
      ...(from ? { from } : {}),
      ...(to ? { to } : {}),
    }).toString()}` ,
    token,
  );

export const createAdminAbsence = (payload: CreateAbsencePayload, token?: string | null) =>
  apiPost<Absence>('/admin/absences', payload, token);

export const updateAdminAbsence = (absenceId: number, payload: UpdateAbsencePayload, token?: string | null) =>
  apiPatch<Absence>(`/admin/absences/${absenceId}`, payload, token);

export const deleteAdminAbsence = (absenceId: number, token?: string | null) =>
  apiDelete<void>(`/admin/absences/${absenceId}`, token);
