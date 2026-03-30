import type { ExportFormat } from '../hooks/useReportExport';

export function ReportExportActions({
  disabled,
  onExport,
}: {
  disabled: boolean;
  onExport: (format: ExportFormat) => void;
}) {
  return (
    <>
      <button type="button" className="btn outline" disabled={disabled} onClick={() => onExport('csv')}>
        {disabled ? 'Exporting…' : 'Export CSV'}
      </button>
      <button type="button" className="btn outline" disabled={disabled} onClick={() => onExport('pdf')}>
        {disabled ? 'Exporting…' : 'Export PDF'}
      </button>
    </>
  );
}
