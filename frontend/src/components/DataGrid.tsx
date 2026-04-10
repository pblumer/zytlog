import { useMemo, useState } from 'react';
import type { ReactNode } from 'react';

export type DataGridColumn<TData> = {
  id: string;
  header: string;
  cell: (row: TData) => ReactNode;
  sortValue?: (row: TData) => string | number;
  searchableText?: (row: TData) => string;
  sortable?: boolean;
};

export type DataGridProps<TData> = {
  columns: DataGridColumn<TData>[];
  data: TData[];
  loading?: boolean;
  error?: string | null;
  emptyTitle?: string;
  emptyDescription?: string;
  searchPlaceholder?: string;
  toolbarRight?: ReactNode;
  initialPageSize?: number;
  getRowClassName?: (row: TData) => string | undefined;
};

export function DataGrid<TData>({
  columns,
  data,
  loading,
  error,
  emptyTitle = 'Keine Einträge gefunden',
  emptyDescription,
  searchPlaceholder = 'Zeilen suchen…',
  toolbarRight,
  initialPageSize = 10,
  getRowClassName,
  rowId,
}: DataGridProps<TData>) {
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState<{ id: string; direction: 'asc' | 'desc' } | null>(null);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(initialPageSize);

  const filteredRows = useMemo(() => {
    if (!search.trim()) return data;
    const searchValue = search.toLowerCase();
    return data.filter((row) =>
      columns.some((column) => {
        const text = (column.searchableText?.(row) ?? '').toLowerCase();
        return text.includes(searchValue);
      }),
    );
  }, [columns, data, search]);

  const sortedRows = useMemo(() => {
    if (!sort) return filteredRows;
    const column = columns.find((currentColumn) => currentColumn.id === sort.id);
    if (!column?.sortValue) return filteredRows;

    const multiplier = sort.direction === 'asc' ? 1 : -1;
    return [...filteredRows].sort((a, b) => {
      const aValue = column.sortValue?.(a);
      const bValue = column.sortValue?.(b);
      if (aValue === bValue) return 0;
      if (aValue === undefined) return 1;
      if (bValue === undefined) return -1;
      return aValue > bValue ? multiplier : -multiplier;
    });
  }, [columns, filteredRows, sort]);

  const totalPages = Math.max(1, Math.ceil(sortedRows.length / pageSize));
  const safePage = Math.min(page, totalPages - 1);
  const pageRows = useMemo(() => {
    const start = safePage * pageSize;
    return sortedRows.slice(start, start + pageSize);
  }, [pageSize, safePage, sortedRows]);

  const toggleSort = (columnId: string) => {
    setPage(0);
    setSort((current) => {
      if (!current || current.id !== columnId) return { id: columnId, direction: 'asc' };
      if (current.direction === 'asc') return { id: columnId, direction: 'desc' };
      return null;
    });
  };

  const colSpan = columns.length || 1;
  const sortDescription = sort ? `${sort.id} ${sort.direction === 'asc' ? 'aufsteigend' : 'absteigend'}` : 'keine Sortierung';

  return (
    <div className="data-grid">
      <div className="data-grid-toolbar">
        <input
          className="data-grid-search"
          value={search}
          onChange={(event) => {
            setSearch(event.target.value);
            setPage(0);
          }}
          placeholder={searchPlaceholder}
          aria-label="Tabellenzeilen suchen"
        />
        {toolbarRight ? <div>{toolbarRight}</div> : null}
      </div>

      <div className="table-wrap">
        <table className="table data-grid-table">
          <caption className="sr-only">Datentabelle, aktuell {sortDescription}</caption>
          <thead>
            <tr>
              {columns.map((column) => {
                const sortDirection = sort?.id === column.id ? sort.direction : null;
                return (
                  <th key={column.id} aria-sort={sortDirection === 'asc' ? 'ascending' : sortDirection === 'desc' ? 'descending' : 'none'}>
                    <button
                      type="button"
                      className={column.sortable ? 'sort-header' : 'plain-header'}
                      onClick={column.sortable ? () => toggleSort(column.id) : undefined}
                      disabled={!column.sortable}
                      aria-label={column.sortable ? `${column.header} sortieren` : undefined}
                    >
                      {column.header}
                      {sortDirection === 'asc' ? ' ↑' : sortDirection === 'desc' ? ' ↓' : ''}
                    </button>
                  </th>
                );
              })}
            </tr>
          </thead>

          <tbody>
            {loading ? (
              <tr>
                <td colSpan={colSpan}>
                  <div className="table-state">Zeilen werden geladen…</div>
                </td>
              </tr>
            ) : error ? (
              <tr>
                <td colSpan={colSpan}>
                  <div className="table-state table-state-error">{error}</div>
                </td>
              </tr>
            ) : pageRows.length === 0 ? (
              <tr>
                <td colSpan={colSpan}>
                  <div className="table-state">
                    <strong>{emptyTitle}</strong>
                    {emptyDescription ? <div className="meta">{emptyDescription}</div> : null}
                  </div>
                </td>
              </tr>
            ) : (
              pageRows.map((row, rowIndex) => (
                <tr key={rowIndex} className={getRowClassName?.(row)}>
                  {columns.map((column) => (
                    <td key={column.id}>{column.cell(row)}</td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="data-grid-pagination">
        <span className="meta">
          Anzeige {pageRows.length} von {sortedRows.length} gefilterte Zeilen
        </span>
        <div className="actions">
          <button type="button" className="btn outline" onClick={() => setPage((current) => Math.max(0, current - 1))} disabled={safePage <= 0}>
            Zurück
          </button>
          <button
            type="button"
            className="btn outline"
            onClick={() => setPage((current) => Math.min(totalPages - 1, current + 1))}
            disabled={safePage >= totalPages - 1}
          >
            Weiter
          </button>
          <select
            value={pageSize}
            aria-label="Zeilen pro Seite"
            onChange={(event) => {
              setPageSize(Number(event.target.value));
              setPage(0);
            }}
          >
            {[10, 20, 50].map((size) => (
              <option key={size} value={size}>
                {size} pro Seite
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}
