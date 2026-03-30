export type UserRole = 'admin' | 'team_lead' | 'employee';

export type Me = {
  user_id: number;
  username: string | null;
  email: string;
  role: UserRole;
  tenant_id: number;
};

export type ClockStatus = 'clocked_in' | 'clocked_out';
export type TimeStampEventType = 'clock_in' | 'clock_out';

export type TimeStampEvent = {
  id: number;
  tenant_id: number;
  employee_id: number;
  timestamp: string;
  type: TimeStampEventType;
  source: string;
  comment: string | null;
  created_at: string;
  updated_at: string;
};

export type CurrentClockStatus = {
  employee_id: number;
  status: ClockStatus;
  last_event_type: TimeStampEventType | null;
  last_event_timestamp: string | null;
};

export type DailyAccountStatus = 'empty' | 'complete' | 'incomplete' | 'invalid';

export type DailyTimeAccount = {
  date: string;
  target_minutes: number;
  actual_minutes: number;
  break_minutes: number;
  balance_minutes: number;
  status: DailyAccountStatus;
  event_count: number;
};

export type DailyOverviewRow = DailyTimeAccount;

export type OverviewTotals = {
  target_minutes: number;
  actual_minutes: number;
  break_minutes: number;
  balance_minutes: number;
  days_total: number;
  days_complete: number;
  days_incomplete: number;
  days_invalid: number;
  days_empty: number;
};

export type WeeklyOverview = {
  iso_year: number;
  iso_week: number;
  range_start: string;
  range_end: string;
  days: DailyOverviewRow[];
  totals: OverviewTotals;
};

export type MonthlyOverview = {
  year: number;
  month: number;
  range_start: string;
  range_end: string;
  days: DailyOverviewRow[];
  totals: OverviewTotals;
};

export type MonthlySummaryRow = {
  month: number;
  target_minutes: number;
  actual_minutes: number;
  break_minutes: number;
  balance_minutes: number;
  days_total: number;
  days_complete: number;
  days_incomplete: number;
  days_invalid: number;
  days_empty: number;
};

export type YearlyOverview = {
  year: number;
  months: MonthlySummaryRow[];
  totals: OverviewTotals;
};

export type Employee = {
  id: number;
  tenant_id: number;
  user_id: number;
  employee_number: string | null;
  first_name: string;
  last_name: string;
  employment_percentage: number;
  entry_date: string;
  exit_date: string | null;
  working_time_model_id: number | null;
  team: string | null;
  created_at: string;
  updated_at: string;
};

export type WorkingTimeModel = {
  id: number;
  tenant_id: number;
  name: string;
  weekly_target_hours: number;
  workdays_per_week: number;
  annual_target_hours: number | null;
  active: boolean;
  created_at: string;
  updated_at: string;
};
