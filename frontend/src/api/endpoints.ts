import { apiDownload, apiGet, apiPatch, apiPost } from './client';
import type {
  CurrentClockStatus,
  DailyTimeAccount,
  Employee,
  Me,
  MonthlyOverview,
  TimeStampEvent,
  WeeklyOverview,
  WorkingTimeModel,
  YearlyOverview,
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

export const downloadDayExport = (date: string, format: 'csv' | 'pdf', token?: string | null) =>
  apiDownload(`/exports/my/day${format === 'pdf' ? '/pdf' : ''}?date=${encodeURIComponent(date)}`, token);

export const downloadWeekExport = (year: number, week: number, format: 'csv' | 'pdf', token?: string | null) =>
  apiDownload(`/exports/my/week${format === 'pdf' ? '/pdf' : ''}?year=${year}&week=${week}`, token);

export const downloadMonthExport = (year: number, month: number, format: 'csv' | 'pdf', token?: string | null) =>
  apiDownload(`/exports/my/month${format === 'pdf' ? '/pdf' : ''}?year=${year}&month=${month}`, token);

export const downloadYearExport = (year: number, format: 'csv' | 'pdf', token?: string | null) =>
  apiDownload(`/exports/my/year${format === 'pdf' ? '/pdf' : ''}?year=${year}`, token);

export const getEmployees = (token?: string | null) => apiGet<Employee[]>('/employees', token);

export const getWorkingTimeModels = (token?: string | null) => apiGet<WorkingTimeModel[]>('/working-time-models', token);

export const clockIn = (token?: string | null) => apiPost<TimeStampEvent>('/time-stamps/clock-in', undefined, token);

export const clockOut = (token?: string | null) => apiPost<TimeStampEvent>('/time-stamps/clock-out', undefined, token);

export type UpdateTimeStampPayload = {
  timestamp: string;
  comment: string | null;
};

export const updateTimeStamp = (eventId: number, payload: UpdateTimeStampPayload, token?: string | null) =>
  apiPatch<TimeStampEvent>(`/time-stamps/${eventId}`, payload, token);
