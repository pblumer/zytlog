export function formatDate(value: string | null | undefined): string {
  if (!value) return '—';
  return new Date(value).toLocaleDateString();
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return '—';
  return new Date(value).toLocaleString();
}

export function isoDate(value: Date): string {
  return value.toISOString().slice(0, 10);
}

export function getIsoWeek(date = new Date()): { year: number; week: number } {
  const target = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  const dayNr = (target.getUTCDay() + 6) % 7;
  target.setUTCDate(target.getUTCDate() - dayNr + 3);
  const firstThursday = new Date(Date.UTC(target.getUTCFullYear(), 0, 4));
  const diff = target.getTime() - firstThursday.getTime();
  const week = 1 + Math.round(diff / 86400000 / 7);
  return { year: target.getUTCFullYear(), week };
}

export function formatMinutes(minutes: number): string {
  const sign = minutes < 0 ? '-' : '';
  const absolute = Math.abs(minutes);
  const hours = Math.floor(absolute / 60)
    .toString()
    .padStart(2, '0');
  const mins = (absolute % 60).toString().padStart(2, '0');
  return `${sign}${hours}:${mins}`;
}
