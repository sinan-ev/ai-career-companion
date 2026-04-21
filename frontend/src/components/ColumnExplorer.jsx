import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Columns3,
  Hash,
  Type,
  Calendar,
  ChevronDown,
  ChevronRight,
  AlertTriangle,
  BarChart3,
  Target,
  Eye,
} from 'lucide-react';

const typeConfig = {
  numeric:     { icon: Hash, color: '#6366f1', bg: 'rgba(99, 102, 241, 0.1)', label: 'Numeric' },
  float64:     { icon: Hash, color: '#6366f1', bg: 'rgba(99, 102, 241, 0.1)', label: 'Numeric' },
  int64:       { icon: Hash, color: '#6366f1', bg: 'rgba(99, 102, 241, 0.1)', label: 'Numeric' },
  categorical: { icon: Type, color: '#ec4899', bg: 'rgba(236, 72, 153, 0.1)', label: 'Categorical' },
  object:      { icon: Type, color: '#ec4899', bg: 'rgba(236, 72, 153, 0.1)', label: 'Categorical' },
  datetime:    { icon: Calendar, color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.1)', label: 'DateTime' },
  boolean:     { icon: Target, color: '#10b981', bg: 'rgba(16, 185, 129, 0.1)', label: 'Boolean' },
  text:        { icon: Type, color: '#8b5cf6', bg: 'rgba(139, 92, 246, 0.1)', label: 'Text' },
  id:          { icon: Hash, color: '#64748b', bg: 'rgba(100, 116, 139, 0.1)', label: 'ID' },
};

const ColumnExplorer = ({ 
  columnTypes = {}, 
  columnReports = {}, 
  columnMeanings = {},
  targetColumn = '',
  featureColumns = [],
  droppedColumns = [],
}) => {
  const [expandedCol, setExpandedCol] = useState(null);
  const [filter, setFilter] = useState('all');

  const columns = Object.keys(columnTypes);
  
  const filteredColumns = columns.filter(col => {
    if (filter === 'all') return true;
    if (filter === 'numeric') return ['numeric', 'float64', 'int64'].includes(columnTypes[col]);
    if (filter === 'categorical') return ['categorical', 'object'].includes(columnTypes[col]);
    if (filter === 'dropped') return droppedColumns.includes(col);
    if (filter === 'features') return featureColumns.includes(col);
    return true;
  });

  const typeCountMap = {};
  columns.forEach(col => {
    const type = columnTypes[col];
    const label = typeConfig[type]?.label || type;
    typeCountMap[label] = (typeCountMap[label] || 0) + 1;
  });

  const toggleExpand = (col) => {
    setExpandedCol(prev => prev === col ? null : col);
  };

  return (
    <div className="col-explorer">
      {/* Filter Bar */}
      <div className="col-filter-bar">
        <div className="col-filters">
          {['all', 'numeric', 'categorical', 'features', 'dropped'].map(f => (
            <button
              key={f}
              className={`col-filter-btn ${filter === f ? 'active' : ''}`}
              onClick={() => setFilter(f)}
            >
              {f === 'all' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1)}
              <span className="filter-count">
                {f === 'all' ? columns.length : 
                 f === 'dropped' ? droppedColumns.length :
                 f === 'features' ? featureColumns.length :
                 filteredColumns.length}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Type Summary */}
      <div className="type-summary">
        {Object.entries(typeCountMap).map(([label, count]) => {
          const config = Object.values(typeConfig).find(c => c.label === label) || { color: '#64748b', bg: 'rgba(100,116,139,0.1)' };
          return (
            <span key={label} className="type-chip" style={{ color: config.color, background: config.bg }}>
              {count} {label}
            </span>
          );
        })}
      </div>

      {/* Column List */}
      <div className="col-list">
        {filteredColumns.map((col, i) => {
          const type = columnTypes[col];
          const config = typeConfig[type] || typeConfig.id;
          const TypeIcon = config.icon;
          const report = columnReports[col] || {};
          const meaning = columnMeanings[col];
          const isTarget = col === targetColumn;
          const isDropped = droppedColumns.includes(col);
          const isExpanded = expandedCol === col;

          return (
            <motion.div
              key={col}
              className={`col-item glass-card ${isExpanded ? 'expanded' : ''} ${isTarget ? 'is-target' : ''} ${isDropped ? 'is-dropped' : ''}`}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.03 }}
            >
              <div className="col-item-header" onClick={() => toggleExpand(col)}>
                <div className="col-item-left">
                  <div className="col-type-icon" style={{ background: config.bg, color: config.color }}>
                    <TypeIcon size={14} />
                  </div>
                  <div className="col-item-info">
                    <span className="col-item-name">{col}</span>
                    <span className="col-item-type">{config.label}</span>
                  </div>
                </div>
                <div className="col-item-right">
                  {isTarget && <span className="target-badge">🎯 Target</span>}
                  {isDropped && <span className="dropped-badge">Dropped</span>}
                  {report.missing_pct != null && report.missing_pct > 0 && (
                    <span className="missing-indicator">
                      <AlertTriangle size={12} />
                      {Number(report.missing_pct).toFixed(1)}% null
                    </span>
                  )}
                  {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                </div>
              </div>

              <AnimatePresence>
                {isExpanded && (
                  <motion.div
                    className="col-detail"
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.25 }}
                  >
                    {meaning && (
                      <div className="col-meaning">
                        <Eye size={13} /> <span>{meaning}</span>
                      </div>
                    )}
                    <div className="col-stats-grid">
                      {report.dtype && <StatItem label="dtype" value={report.dtype} />}
                      {report.unique != null && <StatItem label="Unique" value={report.unique} />}
                      {report.missing_count != null && <StatItem label="Missing" value={report.missing_count} />}
                      {report.mean != null && <StatItem label="Mean" value={Number(report.mean).toFixed(2)} />}
                      {report.std != null && <StatItem label="Std" value={Number(report.std).toFixed(2)} />}
                      {report.min != null && <StatItem label="Min" value={report.min} />}
                      {report.max != null && <StatItem label="Max" value={report.max} />}
                      {report.median != null && <StatItem label="Median" value={report.median} />}
                      {report.skewness != null && <StatItem label="Skewness" value={Number(report.skewness).toFixed(3)} />}
                      {report.outlier_count != null && <StatItem label="Outliers" value={report.outlier_count} />}
                      {report.top_values && (
                        <div className="top-values-section">
                          <span className="stat-label">Top Values</span>
                          <div className="top-values-list">
                            {Object.entries(report.top_values).slice(0, 5).map(([val, count]) => (
                              <span key={val} className="top-val-chip">{val} ({count})</span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          );
        })}
      </div>

      <style>{`
        .col-explorer {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .col-filter-bar {
          display: flex;
          align-items: center;
          justify-content: space-between;
        }

        .col-filters {
          display: flex;
          gap: 6px;
          flex-wrap: wrap;
        }

        .col-filter-btn {
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid var(--glass-border);
          color: var(--text-dim);
          padding: 6px 14px;
          border-radius: var(--radius-full);
          font-family: inherit;
          font-size: 13px;
          font-weight: 500;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 6px;
          transition: all var(--transition-fast);
        }

        .col-filter-btn:hover {
          background: rgba(99, 102, 241, 0.08);
          color: var(--text);
        }

        .col-filter-btn.active {
          background: rgba(99, 102, 241, 0.15);
          border-color: rgba(99, 102, 241, 0.3);
          color: var(--primary);
        }

        .filter-count {
          font-size: 11px;
          font-family: var(--font-mono);
          background: rgba(255, 255, 255, 0.06);
          padding: 1px 6px;
          border-radius: var(--radius-full);
        }

        .type-summary {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
        }

        .type-chip {
          padding: 4px 12px;
          border-radius: var(--radius-full);
          font-size: 12px;
          font-weight: 600;
        }

        .col-list {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .col-item {
          border-radius: var(--radius-md);
          overflow: hidden;
          cursor: pointer;
          transition: border-color var(--transition-fast);
        }

        .col-item.is-target {
          border-color: rgba(16, 185, 129, 0.3);
        }

        .col-item.is-dropped {
          opacity: 0.5;
        }

        .col-item-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 12px 16px;
          gap: 12px;
        }

        .col-item-left {
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .col-type-icon {
          width: 32px;
          height: 32px;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }

        .col-item-info {
          display: flex;
          flex-direction: column;
        }

        .col-item-name {
          font-weight: 600;
          font-size: 14px;
          color: var(--text);
        }

        .col-item-type {
          font-size: 11px;
          color: var(--text-muted);
        }

        .col-item-right {
          display: flex;
          align-items: center;
          gap: 10px;
          color: var(--text-muted);
        }

        .target-badge {
          font-size: 11px;
          font-weight: 600;
          padding: 3px 10px;
          border-radius: var(--radius-full);
          background: rgba(16, 185, 129, 0.1);
          color: #10b981;
        }

        .dropped-badge {
          font-size: 11px;
          font-weight: 600;
          padding: 3px 10px;
          border-radius: var(--radius-full);
          background: rgba(239, 68, 68, 0.1);
          color: #ef4444;
        }

        .missing-indicator {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 11px;
          color: var(--warning);
          font-weight: 500;
        }

        .col-detail {
          overflow: hidden;
          border-top: 1px solid var(--glass-border);
        }

        .col-meaning {
          display: flex;
          align-items: flex-start;
          gap: 8px;
          padding: 12px 16px;
          background: rgba(99, 102, 241, 0.03);
          font-size: 13px;
          color: var(--text-dim);
          line-height: 1.5;
        }

        .col-meaning svg {
          flex-shrink: 0;
          margin-top: 2px;
          color: var(--primary);
        }

        .col-stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
          gap: 1px;
          padding: 12px 16px;
          background: rgba(0, 0, 0, 0.1);
        }

        .stat-item {
          display: flex;
          flex-direction: column;
          gap: 2px;
          padding: 8px 10px;
          border-radius: 6px;
          background: rgba(255, 255, 255, 0.02);
        }

        .stat-label {
          font-size: 10px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          color: var(--text-muted);
          font-weight: 600;
        }

        .stat-value {
          font-size: 14px;
          font-weight: 600;
          color: var(--text);
          font-family: var(--font-mono);
        }

        .top-values-section {
          grid-column: 1 / -1;
          padding: 8px 10px;
        }

        .top-values-list {
          display: flex;
          gap: 6px;
          flex-wrap: wrap;
          margin-top: 6px;
        }

        .top-val-chip {
          background: rgba(255, 255, 255, 0.04);
          border: 1px solid rgba(255, 255, 255, 0.06);
          padding: 3px 10px;
          border-radius: var(--radius-full);
          font-size: 12px;
          color: var(--text-dim);
          font-family: var(--font-mono);
        }
      `}</style>
    </div>
  );
};

const StatItem = ({ label, value }) => (
  <div className="stat-item">
    <span className="stat-label">{label}</span>
    <span className="stat-value">{value}</span>
  </div>
);

export default ColumnExplorer;
