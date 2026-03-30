import { useState } from 'react';

import { useAuth } from '../auth/provider';
import { downloadDayExport, downloadMonthExport, downloadWeekExport, downloadYearExport } from '../api/endpoints';

export type ExportFormat = 'csv' | 'pdf';

function triggerBrowserDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export function useReportExport() {
  const { token } = useAuth();
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async (action: () => Promise<{ blob: Blob; filename?: string }>, fallbackFilename: string) => {
    setIsExporting(true);
    setError(null);
    try {
      const { blob, filename } = await action();
      triggerBrowserDownload(blob, filename ?? fallbackFilename);
    } catch (exportError) {
      const message = exportError instanceof Error ? exportError.message : 'Export failed.';
      setError(message);
    } finally {
      setIsExporting(false);
    }
  };

  return {
    isExporting,
    error,
    clearError: () => setError(null),
    exportDay: (date: string, format: ExportFormat) =>
      run(() => downloadDayExport(date, format, token), `zytlog_day_${date}.${format}`),
    exportWeek: (year: number, week: number, format: ExportFormat) =>
      run(() => downloadWeekExport(year, week, format, token), `zytlog_week_${year}_w${String(week).padStart(2, '0')}.${format}`),
    exportMonth: (year: number, month: number, format: ExportFormat) =>
      run(() => downloadMonthExport(year, month, format, token), `zytlog_month_${year}-${String(month).padStart(2, '0')}.${format}`),
    exportYear: (year: number, format: ExportFormat) =>
      run(() => downloadYearExport(year, format, token), `zytlog_year_${year}.${format}`),
  };
}
