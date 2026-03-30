import type { ReactNode } from 'react';

export function TotalsBar({ items }: { items: Array<{ label: string; value: ReactNode }> }) {
  return (
    <div className="totals-bar">
      {items.map((item) => (
        <div key={item.label} className="totals-item">
          <span className="meta">{item.label}</span>
          <strong>{item.value}</strong>
        </div>
      ))}
    </div>
  );
}
