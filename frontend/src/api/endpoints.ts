import { apiGet, apiPost } from './client';
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

export const getEmployees = (token?: string | null) => apiGet<Employee[]>('/employees', token);

export const getWorkingTimeModels = (token?: string | null) => apiGet<WorkingTimeModel[]>('/working-time-models', token);

export const clockIn = (token?: string | null) => apiPost<TimeStampEvent>('/time-stamps/clock-in', undefined, token);

export const clockOut = (token?: string | null) => apiPost<TimeStampEvent>('/time-stamps/clock-out', undefined, token);
