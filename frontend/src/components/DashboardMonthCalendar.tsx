import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import type { CalendarMonthDay, CalendarDayStatus } from '../types/api';
import { formatMinutes } from '../utils/date';

type Props = {
  year: number;
  month: number;
  days: CalendarMonthDay[];
};

const WEEKDAY_LABELS = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];

function statusClassName(status: CalendarDayStatus) {
  switch (status) {
    case 'complete':
      return 'calendar-tile-complete';
    case 'incomplete':
      return 'calendar-tile-incomplete';
    case 'invalid':
      return 'calendar-tile-invalid';
    default:
      return 'calendar-tile-no-data';
  }
}

export function DashboardMonthCalendar({ year, month, days }: Props) {
  const navigate = useNavigate();
  const byDate = useMemo(() => new Map(days.map((day) => [day.date, day])), [days]);
  const todayIso = new Date().toISOString().slice(0, 10);

  const firstOfMonth = new Date(Date.UTC(year, month - 1, 1));
  const firstWeekday = (firstOfMonth.getUTCDay() + 6) % 7;
  const monthLength = new Date(Date.UTC(year, month, 0)).getUTCDate();
  const cells = [];

  for (let i = 0; i < firstWeekday; i += 1) cells.push(<div key={`empty-${i}`} className="calendar-empty" />);

  for (let dayNumber = 1; dayNumber <= monthLength; dayNumber += 1) {
    const iso = `${year}-${String(month).padStart(2, '0')}-${String(dayNumber).padStart(2, '0')}`;
    const day = byDate.get(iso);
    const status = day?.status ?? 'no_data';

    cells.push(
      <button
        key={iso}
        type="button"
        className={`calendar-tile ${statusClassName(status)} ${iso === todayIso ? 'calendar-tile-today' : ''}`}
        onClick={() => navigate(`/day?date=${iso}`)}
        title={`${iso} · ${status}`}
      >
        <span className="calendar-day-number">{dayNumber}</span>
        <span className="calendar-day-minutes">{day ? formatMinutes(day.actual_minutes) : '—'}</span>
      </button>,
    );
  }

  return (
    <section className="card" style={{ marginTop: '1rem' }}>
      <div className="calendar-header">
        <h3>Monatsübersicht</h3>
        <p className="meta">Status pro Tag, klickbar zur Tagesansicht</p>
      </div>
      <div className="calendar-grid">
        {WEEKDAY_LABELS.map((weekday) => (
          <div key={weekday} className="calendar-weekday">
            {weekday}
          </div>
        ))}
        {cells}
      </div>
    </section>
  );
}
