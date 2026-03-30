import type { ReactNode } from 'react';

export type Column<T> = {
  key: string;
  header: string;
  render: (item: T) => ReactNode;
};

export function SimpleTable<T>({ columns, data, rowKey }: { columns: Column<T>[]; data: T[]; rowKey: (item: T) => string }) {
  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key}>{column.header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((item) => (
            <tr key={rowKey(item)}>
              {columns.map((column) => (
                <td key={column.key}>{column.render(item)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
