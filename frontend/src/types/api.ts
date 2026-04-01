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
export type CalendarDayStatus = 'no_data' | 'complete' | 'incomplete' | 'invalid';
export type DayAbsenceContext = {
  type: 'vacation' | 'sickness';
  label: string;
  duration_type: 'full_day' | 'half_day_am' | 'half_day_pm';
};

export type DailyTimeAccount = {
  date: string;
  target_minutes: number;
  actual_minutes: number;
  break_minutes: number;
  balance_minutes: number;
  status: DailyAccountStatus;
  event_count: number;
  is_holiday: boolean;
  holiday_name: string | null;
  is_workday: boolean;
  absence: DayAbsenceContext | null;
  is_in_non_working_period: boolean;
  non_working_period_label: string | null;
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

export type CalendarMonthDay = {
  date: string;
  status: CalendarDayStatus;
  target_minutes: number;
  actual_minutes: number;
  balance_minutes: number;
  event_count: number;
  absence: DayAbsenceContext | null;
  is_in_non_working_period: boolean;
  non_working_period_label: string | null;
};

export type CalendarMonth = {
  year: number;
  month: number;
  days: CalendarMonthDay[];
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
  created_at: string;
  updated_at: string;
};

export type EmployeeUserOption = {
  id: number;
  email: string;
  full_name: string;
  keycloak_user_id: string;
  role: UserRole;
  has_employee: boolean;
};

export type WorkingTimeModel = {
  id: number;
  tenant_id: number;
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
  created_at: string;
  updated_at: string;
};

export type Holiday = {
  id: number;
  tenant_id: number;
  holiday_set_id: number;
  date: string;
  name: string;
  active: boolean;
  created_at: string;
  updated_at: string;
};

export type HolidaySet = {
  id: number;
  tenant_id: number;
  name: string;
  description: string | null;
  country_code: string | null;
  region_code: string | null;
  source: string | null;
  active: boolean;
  holiday_count: number;
  created_at: string;
  updated_at: string;
};

export type OpenHolidaysCountry = {
  iso_code: string;
  name: string | null;
};

export type OpenHolidaysLanguage = {
  language_code: string;
  name: string | null;
};

export type OpenHolidaysSubdivision = {
  code: string;
  name: string | null;
};

export type OpenHolidaysImportMode = 'skip_existing' | 'replace_existing_in_range';

export type OpenHolidaysImportPayload = {
  country_iso_code: string;
  subdivision_code: string | null;
  language_code: string;
  valid_from: string;
  valid_to: string;
  import_mode: OpenHolidaysImportMode;
};

export type OpenHolidaysImportPreviewRow = {
  date: string;
  name: string;
  country_iso_code: string;
  subdivision_code: string | null;
  language_code: string;
  source: string;
  exists_in_holiday_set: boolean;
  existing_holiday_id: number | null;
  action_hint: 'create' | 'skip' | 'replace';
};

export type OpenHolidaysImportPreview = {
  rows: OpenHolidaysImportPreviewRow[];
};

export type OpenHolidaysImportCommitResult = {
  created: number;
  skipped: number;
  replaced: number;
};

export type AbsenceType = 'vacation' | 'sickness';
export type AbsenceDurationType = 'full_day' | 'half_day_am' | 'half_day_pm';

export type Absence = {
  id: number;
  tenant_id: number;
  employee_id: number;
  absence_type: AbsenceType;
  start_date: string;
  end_date: string;
  duration_type: AbsenceDurationType;
  note: string | null;
  created_at: string;
  updated_at: string;
};

export type NonWorkingPeriodSet = {
  id: number;
  tenant_id: number;
  name: string;
  description: string | null;
  active: boolean;
  period_count: number;
  created_at: string;
  updated_at: string;
};

export type NonWorkingPeriod = {
  id: number;
  tenant_id: number;
  non_working_period_set_id: number;
  start_date: string;
  end_date: string;
  name: string;
  category: string | null;
  created_at: string;
  updated_at: string;
};
