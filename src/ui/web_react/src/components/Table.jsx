import React from 'react';

/**
 * 15-SHARED-CONTRACTS.md §13.1 Table Primitive
 * Density: compact (32px rows) vs comfortable (44px rows) per 07-UX §4.3
 * Supports loading skeletons and empty states.
 */
export default function Table({
  columns = [],
  rows = [],
  emptyState = 'No records found.',
  loading = false,
  onRowClick,
  density = 'comfortable',
  className = '',
}) {
  const rowHeight = density === 'compact' ? '32px' : '44px';
  const cellPadding = density === 'compact' ? '0.35rem 0.75rem' : '0.65rem 1rem';

  if (loading) {
    return (
      <div className="table-responsive">
        <table className={`custom-table ${className}`}>
          <thead>
            <tr>
              {columns.map((col, idx) => (
                <th key={col.key || idx} style={{ width: col.width, textAlign: col.align || 'left' }}>
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {[1, 2, 3, 4].map((n) => (
              <tr key={n} style={{ height: rowHeight }}>
                {columns.map((col, idx) => (
                  <td key={col.key || idx} style={{ padding: cellPadding }}>
                    <div style={{
                      height: '14px',
                      background: 'var(--surface-2)',
                      borderRadius: 'var(--radius-sm)',
                      width: idx === 0 ? '40%' : '75%',
                      animation: 'pulse 1.5s infinite ease-in-out',
                    }} />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  if (!rows || rows.length === 0) {
    return (
      <div className="table-responsive">
        <table className={`custom-table ${className}`}>
          <thead>
            <tr>
              {columns.map((col, idx) => (
                <th key={col.key || idx} style={{ width: col.width, textAlign: col.align || 'left' }}>
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr>
              <td colSpan={columns.length} style={{ textAlign: 'center', padding: '2.5rem 1rem', color: 'var(--ink-3)' }}>
                {typeof emptyState === 'string' ? (
                  <p style={{ margin: 0, fontSize: 'var(--t-body-size)' }}>{emptyState}</p>
                ) : (
                  emptyState
                )}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    );
  }

  return (
    <div className="table-responsive">
      <table className={`custom-table ${className}`}>
        <thead>
          <tr>
            {columns.map((col, idx) => (
              <th key={col.key || idx} style={{ width: col.width, textAlign: col.align || 'left' }}>
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rIdx) => {
            const rowKey = row.id || row.key || row.sku || row.po_number || row.signal_id || row.decision_id || rIdx;
            return (
              <tr
                key={rowKey}
                onClick={() => onRowClick && onRowClick(row)}
                style={{
                  height: rowHeight,
                  cursor: onRowClick ? 'pointer' : 'default',
                }}
              >
                {columns.map((col, cIdx) => {
                  const val = row[col.key];
                  return (
                    <td
                      key={col.key || cIdx}
                      style={{
                        padding: cellPadding,
                        textAlign: col.align || 'left',
                      }}
                    >
                      {col.render ? col.render(val, row) : (val !== null && val !== undefined ? String(val) : '—')}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
