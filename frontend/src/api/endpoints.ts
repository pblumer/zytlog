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
} from '../types/api';

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


export const getHolidays = (token?: string | null, year?: number) =>
  apiGet<Holiday[]>(`/holidays${year ? `?year=${year}` : ""}`, token);

export type CreateHolidayPayload = {
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
