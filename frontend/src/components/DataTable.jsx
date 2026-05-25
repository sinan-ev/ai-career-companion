import React, { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Search, ChevronUp, ChevronDown, ArrowUpDown, Hash, Type, Calendar } from 'lucide-react';

const DataTable = ({ data, columnTypes = {} }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
  const [currentPage, setCurrentPage] = useState(0);
  const rowsPerPage = 10;

  const headers = data && data.length > 0 ? Object.keys(data[0]) : [];

  const getTypeIcon = (header) => {
    const type = columnTypes[header];
    if (type === 'numeric' || type === 'float64' || type === 'int64') return <Hash size={12} />;
    if (type === 'datetime') return <Calendar size={12} />;
    return <Type size={12} />;
  };

  const getTypeColor = (header) => {
    const type = columnTypes[header];
    if (type === 'numeric' || type === 'float64' || type === 'int64') return '#6366f1';
    if (type === 'datetime') return '#f59e0b';
    if (type === 'categorical' || type === 'object') return '#ec4899';
    return '#64748b';
  };

  const filteredData = useMemo(() => {
    if (!data || data.length === 0) return [];
    if (!searchTerm) return data;
    return data.filter(row =>
      headers.some(h =>
        String(row[h] ?? '').toLowerCase().includes(searchTerm.toLowerCase())
      )
    );
  }, [data, searchTerm, headers]);

  const sortedData = useMemo(() => {
    if (!sortConfig.key) return filteredData;
    return [...filteredData].sort((a, b) => {
      const aVal = a[sortConfig.key];
      const bVal = b[sortConfig.key];
      if (aVal == null) return 1;
      if (bVal == null) return -1;
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortConfig.direction === 'asc' ? aVal - bVal : bVal - aVal;
      }
      return sortConfig.direction === 'asc'
        ? String(aVal).localeCompare(String(bVal))
        : String(bVal).localeCompare(String(aVal));
    });
  }, [filteredData, sortConfig]);

  if (!data || data.length === 0) return (
    <div className="empty-table glass-card">
      <p>No preview data available.</p>
    </div>
  );

  const totalPages = Math.ceil(sortedData.length / rowsPerPage);
  const paginatedData = sortedData.slice(
    currentPage * rowsPerPage,
    (currentPage + 1) * rowsPerPage
  );

  const handleSort = (key) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  return (
    <div className="datatable-wrapper">
      <div className="table-toolbar">
        <div className="search-box">
          <Search size={16} />
          <input
            type="text"
            placeholder="Search rows..."
            value={searchTerm}
            onChange={(e) => { setSearchTerm(e.target.value); setCurrentPage(0); }}
          />
        </div>
        <span className="row-count">{filteredData.length} rows</span>
      </div>

      <div className="table-container glass-card">
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                {headers.map(h => (
                  <th key={h} onClick={() => handleSort(h)}>
                    <div className="th-content">
                      <span className="th-type-dot" style={{ background: getTypeColor(h) }}>
                        {getTypeIcon(h)}
                      </span>
                      <span className="th-label">{h}</span>
                      <span className="th-sort">
                        {sortConfig.key === h ? (
                          sortConfig.direction === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                        ) : (
                          <ArrowUpDown size={12} className="sort-idle" />
                        )}
                      </span>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {paginatedData.map((row, i) => (
                <motion.tr
                  key={i}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: i * 0.02 }}
                >
                  {headers.map(h => {
                    const val = row[h];
                    const isNull = val === null || val === undefined || val === '';
                    return (
                      <td key={h} className={isNull ? 'null-cell' : ''}>
                        {isNull ? <span className="null-badge">NULL</span> : String(val)}
                      </td>
                    );
                  })}
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>

        {totalPages > 1 && (
          <div className="table-pagination">
            <button
              disabled={currentPage === 0}
              onClick={() => setCurrentPage(p => p - 1)}
            >
              ← Prev
            </button>
            <span className="page-info">
              Page {currentPage + 1} of {totalPages}
            </span>
            <button
              disabled={currentPage >= totalPages - 1}
              onClick={() => setCurrentPage(p => p + 1)}
            >
              Next →
            </button>
          </div>
        )}
      </div>

      <style>{`
        .datatable-wrapper {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .table-toolbar {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 16px;
        }

        .search-box {
          display: flex;
          align-items: center;
          gap: 10px;
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid var(--glass-border);
          border-radius: var(--radius-md);
          padding: 8px 14px;
          flex: 1;
          max-width: 320px;
          color: var(--text-dim);
          transition: border-color var(--transition-fast);
        }

        .search-box:focus-within {
          border-color: var(--primary);
        }

        .search-box input {
          background: none;
          border: none;
          outline: none;
          color: var(--text);
          font-family: inherit;
          font-size: 14px;
          width: 100%;
        }

        .search-box input::placeholder {
          color: var(--text-muted);
        }

        .row-count {
          font-size: 13px;
          font-weight: 500;
          color: var(--text-dim);
          font-family: var(--font-mono);
        }

        .table-container {
          overflow: hidden;
          border-radius: var(--radius-lg);
        }

        .table-scroll {
          overflow-x: auto;
          max-height: 480px;
          overflow-y: auto;
        }

        .empty-table {
          padding: 40px;
          text-align: center;
          color: var(--text-dim);
        }

        table {
          width: 100%;
          border-collapse: collapse;
          text-align: left;
          font-size: 13px;
        }

        th {
          padding: 12px 16px;
          color: var(--text-dim);
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          font-size: 11px;
          position: sticky;
          top: 0;
          background: var(--surface);
          z-index: 2;
          cursor: pointer;
          user-select: none;
          transition: color var(--transition-fast);
          border-bottom: 1px solid var(--glass-border);
        }

        th:hover {
          color: var(--text);
        }

        .th-content {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .th-type-dot {
          width: 20px;
          height: 20px;
          border-radius: 5px;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          color: white;
          font-size: 10px;
        }

        .th-label {
          white-space: nowrap;
        }

        .th-sort {
          margin-left: auto;
          opacity: 0.4;
        }

        .sort-idle {
          opacity: 0.3;
        }

        td {
          padding: 10px 16px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.03);
          color: var(--text-dim);
          white-space: nowrap;
          font-family: var(--font-mono);
          font-size: 12.5px;
          transition: background var(--transition-fast), color var(--transition-fast);
        }

        tr:hover td {
          background: rgba(99, 102, 241, 0.03);
          color: var(--text);
        }

        .null-cell {
          color: var(--text-muted);
        }

        .null-badge {
          background: rgba(239, 68, 68, 0.1);
          color: var(--error);
          padding: 2px 8px;
          border-radius: 4px;
          font-size: 10px;
          font-weight: 600;
          letter-spacing: 0.5px;
        }

        .table-pagination {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 16px;
          padding: 12px 20px;
          border-top: 1px solid var(--glass-border);
        }

        .table-pagination button {
          background: rgba(255, 255, 255, 0.04);
          border: 1px solid var(--glass-border);
          color: var(--text-dim);
          padding: 6px 14px;
          border-radius: var(--radius-sm);
          cursor: pointer;
          font-family: inherit;
          font-size: 13px;
          font-weight: 500;
          transition: all var(--transition-fast);
        }

        .table-pagination button:hover:not(:disabled) {
          background: rgba(99, 102, 241, 0.1);
          color: var(--primary);
          border-color: rgba(99, 102, 241, 0.3);
        }

        .table-pagination button:disabled {
          opacity: 0.3;
          cursor: not-allowed;
        }

        .page-info {
          font-size: 13px;
          color: var(--text-dim);
          font-family: var(--font-mono);
        }
      `}</style>
    </div>
  );
};

export default DataTable;
