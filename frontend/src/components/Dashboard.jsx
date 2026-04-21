import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  LayoutDashboard,
  Table,
  Layers,
  BarChart3,
  Sparkles,
  ShieldCheck,
  Download,
  AlertTriangle,
  Columns3,
  Target,
  FileDown,
  ChevronRight,
  ExternalLink,
  Brain,
  Lightbulb,
  ArrowLeft,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
} from 'recharts';
import DataTable from './DataTable';
import PipelineView from './PipelineView';
import ColumnExplorer from './ColumnExplorer';

const BACKEND_URL = 'http://127.0.0.1:8000';

const Dashboard = ({ data, onReset }) => {
  const [activeTab, setActiveTab] = useState('overview');

  if (!data) return null;

  const { module1, module2 } = data;
  const eda = module2.eda_report;
  const overview = eda.overview;
  const outputs = module2.dataset_outputs;

  const tabs = [
    { id: 'overview',  label: 'Overview',   icon: LayoutDashboard },
    { id: 'columns',   label: 'Columns',    icon: Columns3 },
    { id: 'data',      label: 'Data',       icon: Table },
    { id: 'pipeline',  label: 'Pipeline',   icon: Layers },
    { id: 'quality',   label: 'Quality',    icon: ShieldCheck },
    { id: 'exports',   label: 'Exports',    icon: FileDown },
  ];

  // ─── Quality score color ───
  const getGradeColor = (grade) => {
    const map = { A: '#10b981', B: '#3b82f6', C: '#f59e0b', D: '#f97316', F: '#ef4444' };
    return map[grade] || '#64748b';
  };

  const gradeColor = getGradeColor(eda.quality_score.grade);

  // ─── Missing data chart data ───
  const missingData = Object.entries(module1.data_quality.missing_percent || {})
    .filter(([, pct]) => pct > 0)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 12)
    .map(([col, pct]) => ({ name: col, pct: Number(pct.toFixed(1)) }));

  // ─── Column type chart data ───
  const colTypeData = [
    { name: 'Numeric', count: overview.n_numeric || 0, color: '#6366f1' },
    { name: 'Categorical', count: overview.n_categorical || 0, color: '#ec4899' },
    { name: 'DateTime', count: overview.n_datetime || 0, color: '#f59e0b' },
    { name: 'ID', count: overview.n_id || 0, color: '#64748b' },
  ].filter(d => d.count > 0);

  // ─── TAB: Overview ───
  const renderOverview = () => (
    <div className="tab-content animate-fade-in">
      {/* Stat Cards */}
      <div className="stats-grid">
        <StatCard label="Total Rows" value={overview.n_rows?.toLocaleString()} icon={Layers} color="#6366f1" />
        <StatCard label="Columns" value={overview.n_cols} icon={Columns3} color="#ec4899" />
        <StatCard label="Missing" value={`${overview.total_missing_pct}%`} icon={AlertTriangle} color="#f59e0b" />
        <StatCard label="Quality" value={eda.quality_score.grade} subtext={`${eda.quality_score.score}/100`} icon={ShieldCheck} color={gradeColor} />
        <StatCard label="Duplicates" value={module1.data_quality.duplicate_rows} icon={Table} color="#8b5cf6" />
        <StatCard label="Target" value={outputs.target_column || 'N/A'} icon={Target} color="#10b981" small />
      </div>

      {/* AI Insight + Chart Grid */}
      <div className="main-grid">
        {/* AI Summary */}
        <div className="glass-card ai-card">
          <div className="card-header">
            <div className="card-header-left">
              <Brain size={18} strokeWidth={1.5} color="var(--primary)" />
              <h3>AI Intelligence Report</h3>
            </div>
          </div>
          <p className="ai-summary-text">{module1.ai_summary}</p>

          {module1.suggested_analyses && module1.suggested_analyses.length > 0 && (
            <div className="suggestions-block">
              <div className="suggestions-header">
                <Lightbulb size={14} color="#f59e0b" />
                <h4>Suggested Analyses</h4>
              </div>
              <div className="suggestions-list">
                {module1.suggested_analyses.map((s, idx) => (
                  <div key={idx} className="suggestion-item">
                    <ChevronRight size={12} />
                    <span>{s}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Charts Side */}
        <div className="charts-stack">
          {/* Column Types Chart */}
          <div className="glass-card chart-card">
            <div className="card-header">
              <div className="card-header-left">
                <BarChart3 size={18} strokeWidth={1.5} color="var(--secondary)" />
                <h3>Column Types</h3>
              </div>
            </div>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={colTypeData} barSize={36}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="name" stroke="var(--text-muted)" tick={{ fontSize: 12 }} />
                  <YAxis stroke="var(--text-muted)" tick={{ fontSize: 12 }} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                    itemStyle={{ color: '#f1f5f9' }}
                    cursor={{ fill: 'rgba(255,255,255,0.03)' }}
                  />
                  <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                    {colTypeData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Missing Data Chart */}
          {missingData.length > 0 && (
            <div className="glass-card chart-card">
              <div className="card-header">
                <div className="card-header-left">
                  <AlertTriangle size={18} strokeWidth={1.5} color="#f59e0b" />
                  <h3>Missing Data</h3>
                </div>
              </div>
              <div className="chart-container">
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={missingData} layout="vertical" barSize={14}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
                    <XAxis type="number" stroke="var(--text-muted)" tick={{ fontSize: 11 }} unit="%" />
                    <YAxis type="category" dataKey="name" stroke="var(--text-muted)" tick={{ fontSize: 11 }} width={100} />
                    <Tooltip
                      contentStyle={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                      itemStyle={{ color: '#f1f5f9' }}
                      formatter={(val) => `${val}%`}
                    />
                    <Bar dataKey="pct" radius={[0, 4, 4, 0]} fill="#f59e0b" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Schema Summary */}
      <div className="glass-card schema-card">
        <div className="card-header">
          <div className="card-header-left">
            <Columns3 size={18} strokeWidth={1.5} color="var(--cyan)" />
            <h3>Data Schema</h3>
          </div>
        </div>
        <div className="schema-grid">
          <SchemaBlock title="Numeric" columns={module1.data_schema.numeric} color="#6366f1" />
          <SchemaBlock title="Categorical" columns={module1.data_schema.categorical} color="#ec4899" />
          <SchemaBlock title="DateTime" columns={module1.data_schema.datetime} color="#f59e0b" />
          {module1.data_schema.unknown && module1.data_schema.unknown.length > 0 && (
            <SchemaBlock title="Unknown" columns={module1.data_schema.unknown} color="#64748b" />
          )}
        </div>
      </div>
    </div>
  );

  // ─── TAB: Quality ───
  const renderQuality = () => (
    <div className="tab-content animate-fade-in">
      <div className="glass-card quality-hero">
        <div className="quality-score-ring" style={{ borderColor: gradeColor }}>
          <span className="quality-grade" style={{ color: gradeColor }}>{eda.quality_score.grade}</span>
          <span className="quality-score-num">{eda.quality_score.score}/100</span>
        </div>
        <div className="quality-text">
          <h3>Data Quality Assessment</h3>
          <p>Based on missing values, duplicates, outliers, and column consistency analysis.</p>
          <div className="quality-meta">
            <span>🧹 {overview.total_missing_pct}% missing</span>
            <span>📊 {module1.data_quality.duplicate_rows} duplicates</span>
            <span>⚠️ {eda.warnings.length} warnings</span>
          </div>
        </div>
      </div>

      {eda.warnings.length > 0 && (
        <div className="warnings-section">
          <h3 className="section-title">⚠️ Warnings & Issues</h3>
          <div className="warnings-list">
            {eda.warnings.map((w, i) => {
              const level = w.level || 'info';
              const levelColor = level === 'critical' ? '#ef4444' : level === 'high' ? '#f97316' : level === 'medium' ? '#f59e0b' : '#3b82f6';
              return (
                <motion.div
                  key={i}
                  className="warning-item glass-card"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                >
                  <span className="warning-level-dot" style={{ background: levelColor }} />
                  <div className="warning-content">
                    <span className="warning-msg">{w.message}</span>
                    <span className="warning-level" style={{ color: levelColor }}>{level}</span>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      )}

      {/* Pipeline warnings */}
      {module2.warnings && module2.warnings.length > 0 && (
        <div className="warnings-section">
          <h3 className="section-title">🔔 Pipeline Warnings</h3>
          <div className="warnings-list">
            {module2.warnings.map((w, i) => (
              <div key={i} className="warning-item glass-card">
                <span className="warning-level-dot" style={{ background: '#f59e0b' }} />
                <div className="warning-content">
                  <span className="warning-msg">{typeof w === 'string' ? w : w.message}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  // ─── TAB: Exports ───
  const renderExports = () => (
    <div className="tab-content animate-fade-in">
      <div className="exports-grid">
        <div className="glass-card export-card">
          <div className="export-icon-bg" style={{ background: 'rgba(99, 102, 241, 0.1)' }}>
            <Table size={24} color="#6366f1" />
          </div>
          <h4>Analytics Dataset</h4>
          <p>Human-readable data for dashboards. Original values preserved.</p>
          <div className="export-meta">
            <span>Shape: {outputs.analytics_shape?.join(' × ')}</span>
          </div>
          {outputs.dataset_files?.analytics && (
            <a
              className="btn-primary export-download-btn"
              href={`${BACKEND_URL}${outputs.dataset_files.analytics}`}
              target="_blank"
              rel="noreferrer"
            >
              <Download size={16} /> Download CSV
            </a>
          )}
        </div>

        <div className="glass-card export-card">
          <div className="export-icon-bg" style={{ background: 'rgba(16, 185, 129, 0.1)' }}>
            <Sparkles size={24} color="#10b981" />
          </div>
          <h4>ML-Ready Dataset</h4>
          <p>Encoded + scaled data ready for machine learning models.</p>
          <div className="export-meta">
            <span>Shape: {outputs.ml_shape?.join(' × ')}</span>
            <span>{outputs.was_encoded ? '✓ Encoded' : '✗ Not encoded'}</span>
            <span>{outputs.was_scaled ? '✓ Scaled' : '✗ Not scaled'}</span>
          </div>
          {outputs.dataset_files?.ml && (
            <a
              className="btn-primary export-download-btn"
              href={`${BACKEND_URL}${outputs.dataset_files.ml}`}
              target="_blank"
              rel="noreferrer"
            >
              <Download size={16} /> Download CSV
            </a>
          )}
        </div>

        <div className="glass-card export-card">
          <div className="export-icon-bg" style={{ background: 'rgba(139, 92, 246, 0.1)' }}>
            <FileDown size={24} color="#8b5cf6" />
          </div>
          <h4>Model Artifacts</h4>
          <p>Fitted encoders & scalers for production inference.</p>
          <div className="export-meta">
            {outputs.artifact_paths && Object.entries(outputs.artifact_paths).map(([k, v]) => (
              <span key={k}>{k}: {v || 'N/A'}</span>
            ))}
          </div>
        </div>
      </div>

      {/* Feature / Dropped columns */}
      <div className="info-grid">
        <div className="glass-card info-block">
          <h4>🎯 Target Column</h4>
          <span className="info-value">{outputs.target_column || 'Not detected'}</span>
        </div>
        <div className="glass-card info-block">
          <h4>📋 Feature Columns ({outputs.feature_columns?.length || 0})</h4>
          <div className="info-chips">
            {(outputs.feature_columns || []).map(c => (
              <span key={c} className="info-chip">{c}</span>
            ))}
          </div>
        </div>
        <div className="glass-card info-block">
          <h4>🗑️ Dropped Columns ({outputs.dropped_columns?.length || 0})</h4>
          <div className="info-chips">
            {(outputs.dropped_columns || []).length > 0 
              ? outputs.dropped_columns.map(c => (
                  <span key={c} className="info-chip dropped">{c}</span>
                ))
              : <span className="info-empty">None dropped</span>
            }
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="dashboard-container animate-fade-in">
      {/* Sidebar */}
      <aside className="sidebar glass-card">
        <div className="sidebar-header">
          <div className="logo-icon">AG</div>
          <div>
            <h2>AI Insights</h2>
            <span className="sidebar-version">v2.0</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          {tabs.map(tab => (
            <button
              key={tab.id}
              className={`nav-item ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <tab.icon size={18} strokeWidth={1.5} />
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <button className="btn-new" onClick={onReset}>
            <ArrowLeft size={16} />
            New Dataset
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="dashboard-main">
        <header className="main-header">
          <div className="header-left">
            <h1>{module1.dataset_info.domain || 'Data Analysis'}</h1>
            <p className="header-meta">
              {module1.dataset_info.file_name} • {overview.n_rows?.toLocaleString()} rows × {overview.n_cols} cols
              {module1.dataset_info.was_sampled && <span className="sampled-badge"> (sampled)</span>}
            </p>
          </div>
          <div className="header-right">
            <div className="status-badge">
              <span className="status-dot" />
              Pipeline Complete
            </div>
            <span className="header-time">{new Date(module2.generated_at).toLocaleTimeString()}</span>
          </div>
        </header>

        {activeTab === 'overview' && renderOverview()}

        {activeTab === 'columns' && (
          <div className="tab-content animate-fade-in">
            <ColumnExplorer
              columnTypes={eda.column_types}
              columnReports={eda.column_reports}
              columnMeanings={module1.column_meanings}
              targetColumn={outputs.target_column}
              featureColumns={outputs.feature_columns}
              droppedColumns={outputs.dropped_columns}
            />
          </div>
        )}

        {activeTab === 'data' && (
          <div className="tab-content animate-fade-in">
            <div className="tab-heading">
              <h3>Processed Data Preview</h3>
              <p>First rows of the analytics dataset (human-readable)</p>
            </div>
            <DataTable
              data={outputs.sample_data}
              columnTypes={eda.column_types}
            />
          </div>
        )}

        {activeTab === 'pipeline' && (
          <div className="tab-content animate-fade-in">
            <PipelineView steps={module2.pipeline_steps} />
          </div>
        )}

        {activeTab === 'quality' && renderQuality()}
        {activeTab === 'exports' && renderExports()}
      </main>

      <style>{`
        .dashboard-container {
          display: flex;
          height: 100vh;
          width: 100vw;
          background: var(--background);
          overflow: hidden;
        }

        /* ─── Sidebar ─── */
        .sidebar {
          width: 260px;
          display: flex;
          flex-direction: column;
          padding: 24px 16px;
          border-radius: 0;
          border-right: 1px solid var(--glass-border);
          border-left: none;
          border-top: none;
          border-bottom: none;
          flex-shrink: 0;
        }

        .sidebar-header {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 0 8px;
          margin-bottom: 32px;
        }

        .logo-icon {
          background: linear-gradient(135deg, var(--primary), var(--accent));
          width: 36px;
          height: 36px;
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 800;
          font-size: 14px;
          color: white;
          flex-shrink: 0;
        }

        .sidebar-header h2 {
          font-size: 17px;
          font-weight: 700;
          color: var(--text);
        }

        .sidebar-version {
          font-size: 11px;
          color: var(--text-muted);
          font-family: var(--font-mono);
        }

        .sidebar-nav {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .nav-item {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 10px 14px;
          border: none;
          background: none;
          color: var(--text-dim);
          border-radius: var(--radius-md);
          cursor: pointer;
          font-weight: 500;
          font-size: 14px;
          transition: all var(--transition-fast);
          text-align: left;
          font-family: inherit;
        }

        .nav-item:hover {
          background: rgba(255, 255, 255, 0.04);
          color: var(--text);
        }

        .nav-item.active {
          background: rgba(99, 102, 241, 0.12);
          color: var(--primary);
          font-weight: 600;
        }

        .sidebar-footer {
          padding-top: 16px;
          border-top: 1px solid var(--glass-border);
        }

        .btn-new {
          width: 100%;
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid var(--glass-border);
          color: var(--text-dim);
          padding: 10px;
          border-radius: var(--radius-md);
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          cursor: pointer;
          font-weight: 500;
          font-family: inherit;
          font-size: 13px;
          transition: all var(--transition-fast);
        }

        .btn-new:hover {
          background: rgba(99, 102, 241, 0.08);
          color: var(--primary);
          border-color: rgba(99, 102, 241, 0.2);
        }

        /* ─── Main ─── */
        .dashboard-main {
          flex: 1;
          display: flex;
          flex-direction: column;
          overflow-y: auto;
          padding: 28px 32px 40px;
        }

        .main-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 28px;
        }

        .header-left h1 {
          font-size: 24px;
          font-weight: 700;
          letter-spacing: -0.5px;
          margin-bottom: 4px;
        }

        .header-meta {
          color: var(--text-dim);
          font-size: 13px;
        }

        .sampled-badge {
          color: var(--warning);
          font-weight: 500;
        }

        .header-right {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .status-badge {
          background: rgba(16, 185, 129, 0.08);
          color: #10b981;
          padding: 6px 14px;
          border-radius: var(--radius-full);
          font-size: 12px;
          font-weight: 600;
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .status-dot {
          width: 6px;
          height: 6px;
          background: #10b981;
          border-radius: 50%;
          animation: pulse-ring 2s infinite;
        }

        .header-time {
          font-size: 12px;
          color: var(--text-muted);
          font-family: var(--font-mono);
        }

        /* ─── Tab Content ─── */
        .tab-content {
          display: flex;
          flex-direction: column;
          gap: 20px;
        }

        .tab-heading {
          margin-bottom: 4px;
        }

        .tab-heading h3 {
          font-size: 18px;
          font-weight: 600;
          margin-bottom: 4px;
        }

        .tab-heading p {
          font-size: 13px;
          color: var(--text-dim);
        }

        /* ─── Stats Grid ─── */
        .stats-grid {
          display: grid;
          grid-template-columns: repeat(6, 1fr);
          gap: 12px;
        }

        @media (max-width: 1200px) {
          .stats-grid {
            grid-template-columns: repeat(3, 1fr);
          }
        }

        .stat-card {
          padding: 18px;
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .stat-icon-box {
          width: 40px;
          height: 40px;
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }

        .stat-info {
          display: flex;
          flex-direction: column;
          min-width: 0;
        }

        .stat-info .stat-label {
          color: var(--text-muted);
          font-size: 11px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .stat-info .stat-value {
          font-size: 20px;
          font-weight: 700;
          color: var(--text);
          line-height: 1.2;
        }

        .stat-info .stat-value.small-val {
          font-size: 14px;
          font-family: var(--font-mono);
        }

        .stat-info .stat-subtext {
          font-size: 11px;
          color: var(--text-dim);
          font-family: var(--font-mono);
        }

        /* ─── Main Grid ─── */
        .main-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 16px;
        }

        @media (max-width: 1100px) {
          .main-grid {
            grid-template-columns: 1fr;
          }
        }

        .charts-stack {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        /* ─── Card Styles ─── */
        .card-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 20px 20px 0;
          margin-bottom: 16px;
        }

        .card-header-left {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .card-header h3 {
          font-size: 15px;
          font-weight: 600;
        }

        .ai-card {
          padding: 0 0 20px;
        }

        .ai-summary-text {
          padding: 0 20px;
          line-height: 1.7;
          color: var(--text-dim);
          font-size: 14px;
        }

        .suggestions-block {
          margin: 16px 20px 0;
          padding: 16px;
          background: rgba(245, 158, 11, 0.03);
          border: 1px solid rgba(245, 158, 11, 0.08);
          border-radius: var(--radius-md);
        }

        .suggestions-header {
          display: flex;
          align-items: center;
          gap: 6px;
          margin-bottom: 10px;
        }

        .suggestions-header h4 {
          font-size: 13px;
          font-weight: 600;
          color: var(--text);
        }

        .suggestions-list {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .suggestion-item {
          display: flex;
          align-items: flex-start;
          gap: 6px;
          font-size: 13px;
          color: var(--text-dim);
          line-height: 1.4;
        }

        .suggestion-item svg {
          flex-shrink: 0;
          margin-top: 3px;
          color: var(--text-muted);
        }

        .chart-card {
          padding: 0 0 16px;
        }

        .chart-container {
          padding: 0 12px;
        }

        /* ─── Schema ─── */
        .schema-card {
          padding: 0 0 20px;
        }

        .schema-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 12px;
          padding: 0 20px;
        }

        .schema-block {
          padding: 14px;
          background: rgba(255, 255, 255, 0.02);
          border-radius: var(--radius-md);
          border: 1px solid rgba(255, 255, 255, 0.04);
        }

        .schema-block-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 10px;
        }

        .schema-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }

        .schema-block-header span {
          font-size: 13px;
          font-weight: 600;
          color: var(--text);
        }

        .schema-block-header .schema-count {
          margin-left: auto;
          font-size: 11px;
          color: var(--text-muted);
          font-family: var(--font-mono);
        }

        .schema-cols {
          display: flex;
          flex-wrap: wrap;
          gap: 4px;
        }

        .schema-col-chip {
          font-size: 11px;
          font-family: var(--font-mono);
          padding: 3px 8px;
          border-radius: 4px;
          background: rgba(255, 255, 255, 0.04);
          color: var(--text-dim);
        }

        /* ─── Quality ─── */
        .quality-hero {
          display: flex;
          align-items: center;
          gap: 28px;
          padding: 32px;
        }

        .quality-score-ring {
          width: 100px;
          height: 100px;
          border-radius: 50%;
          border: 4px solid;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          background: rgba(0, 0, 0, 0.2);
        }

        .quality-grade {
          font-size: 36px;
          font-weight: 800;
          line-height: 1;
        }

        .quality-score-num {
          font-size: 12px;
          color: var(--text-dim);
          font-family: var(--font-mono);
        }

        .quality-text h3 {
          font-size: 18px;
          margin-bottom: 6px;
        }

        .quality-text p {
          font-size: 13px;
          color: var(--text-dim);
          margin-bottom: 12px;
        }

        .quality-meta {
          display: flex;
          gap: 14px;
          font-size: 13px;
          color: var(--text-dim);
        }

        .section-title {
          font-size: 16px;
          font-weight: 600;
          margin-bottom: 12px;
        }

        .warnings-list {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .warning-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px 16px;
          border-radius: var(--radius-md);
        }

        .warning-level-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          flex-shrink: 0;
        }

        .warning-content {
          display: flex;
          align-items: center;
          justify-content: space-between;
          flex: 1;
          gap: 12px;
        }

        .warning-msg {
          font-size: 13px;
          color: var(--text-dim);
        }

        .warning-level {
          font-size: 11px;
          font-weight: 600;
          text-transform: uppercase;
        }

        /* ─── Exports ─── */
        .exports-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 16px;
        }

        @media (max-width: 1100px) {
          .exports-grid {
            grid-template-columns: 1fr;
          }
        }

        .export-card {
          padding: 24px;
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .export-icon-bg {
          width: 48px;
          height: 48px;
          border-radius: var(--radius-md);
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .export-card h4 {
          font-size: 16px;
          font-weight: 600;
        }

        .export-card p {
          font-size: 13px;
          color: var(--text-dim);
          line-height: 1.5;
        }

        .export-meta {
          display: flex;
          flex-direction: column;
          gap: 4px;
          font-size: 12px;
          color: var(--text-muted);
          font-family: var(--font-mono);
        }

        .export-download-btn {
          margin-top: auto;
          justify-content: center;
          text-decoration: none;
          font-size: 14px;
        }

        .info-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 16px;
        }

        @media (max-width: 1100px) {
          .info-grid {
            grid-template-columns: 1fr;
          }
        }

        .info-block {
          padding: 20px;
        }

        .info-block h4 {
          font-size: 14px;
          font-weight: 600;
          margin-bottom: 10px;
        }

        .info-value {
          font-size: 18px;
          font-weight: 700;
          color: var(--primary);
          font-family: var(--font-mono);
        }

        .info-chips {
          display: flex;
          flex-wrap: wrap;
          gap: 4px;
        }

        .info-chip {
          font-size: 11px;
          font-family: var(--font-mono);
          padding: 3px 8px;
          border-radius: 4px;
          background: rgba(99, 102, 241, 0.08);
          color: var(--primary);
        }

        .info-chip.dropped {
          background: rgba(239, 68, 68, 0.08);
          color: var(--error);
        }

        .info-empty {
          font-size: 13px;
          color: var(--text-muted);
        }
      `}</style>
    </div>
  );
};

// ─── Stat Card ───
const StatCard = ({ label, value, subtext, icon: Icon, color, small }) => (
  <div className="glass-card stat-card">
    <div className="stat-icon-box" style={{ backgroundColor: `${color}12`, color }}>
      <Icon size={18} strokeWidth={1.5} />
    </div>
    <div className="stat-info">
      <span className="stat-label">{label}</span>
      <span className={`stat-value ${small ? 'small-val' : ''}`}>{value}</span>
      {subtext && <span className="stat-subtext">{subtext}</span>}
    </div>
  </div>
);

// ─── Schema Block ───
const SchemaBlock = ({ title, columns = [], color }) => (
  <div className="schema-block">
    <div className="schema-block-header">
      <span className="schema-dot" style={{ background: color }} />
      <span>{title}</span>
      <span className="schema-count">{columns.length}</span>
    </div>
    <div className="schema-cols">
      {columns.length > 0
        ? columns.map(c => <span key={c} className="schema-col-chip">{c}</span>)
        : <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>None</span>
      }
    </div>
  </div>
);

export default Dashboard;
