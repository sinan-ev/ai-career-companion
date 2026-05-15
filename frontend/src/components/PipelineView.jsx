import React from 'react';
import { motion } from 'framer-motion';
import {
  CheckCircle2,
  XCircle,
  SkipForward,
  Clock,
  ChevronRight,
  Workflow,
  ArrowRight,
} from 'lucide-react';

const statusConfig = {
  success: { icon: CheckCircle2, color: '#10b981', bg: 'rgba(16, 185, 129, 0.08)', label: 'Completed' },
  failed:  { icon: XCircle, color: '#ef4444', bg: 'rgba(239, 68, 68, 0.08)', label: 'Failed' },
  skipped: { icon: SkipForward, color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.08)', label: 'Skipped' },
};

const stepNameMap = {
  handle_missing:     { label: 'Handle Missing Values', emoji: '🩹' },
  remove_duplicates:  { label: 'Remove Duplicates', emoji: '🗑️' },
  encoding:           { label: 'Categorical Encoding', emoji: '🔢' },
  encode_categorical: { label: 'Categorical Encoding', emoji: '🔢' },
  scaling:            { label: 'Feature Scaling', emoji: '⚖️' },
  scale_numeric:      { label: 'Feature Scaling', emoji: '⚖️' },
  outlier_handling:   { label: 'Outlier Treatment', emoji: '📊' },
  handle_outliers:    { label: 'Outlier Treatment', emoji: '📊' },
  datetime_features:  { label: 'DateTime Features', emoji: '📅' },
  drop_id_columns:    { label: 'Drop ID Columns', emoji: '🏷️' },
  feature_engineering:{ label: 'Feature Engineering', emoji: '⚙️' },
  drop_high_null:     { label: 'Drop High-Null Columns', emoji: '🚫' },
  validate:           { label: 'Input Validation', emoji: '✅' },
};

const PipelineView = ({ steps = [], plan = [] }) => {
  if (!steps || steps.length === 0) {
    return (
      <div className="pipeline-empty glass-card">
        <Workflow size={40} strokeWidth={1.2} />
        <p>No pipeline steps recorded</p>
      </div>
    );
  }

  const successCount = steps.filter(s => s.status === 'success').length;
  const failedCount  = steps.filter(s => s.status === 'failed').length;

  return (
    <div className="pipeline-view">
      {/* Summary Bar */}
      <div className="pipeline-summary glass-card">
        <div className="pipeline-summary-left">
          <Workflow size={20} strokeWidth={1.5} color="var(--primary)" />
          <span className="pipeline-title">AI-Orchestrated Pipeline</span>
        </div>
        <div className="pipeline-summary-stats">
          <span className="stat-pill success-pill">{successCount} passed</span>
          {failedCount > 0 && <span className="stat-pill fail-pill">{failedCount} failed</span>}
          <span className="stat-pill total-pill">{steps.length} steps</span>
        </div>
      </div>

      {/* Module 3 Feature Pills */}
      <div className="pipeline-module3-pills">
        {[
          { emoji: '🔭', label: 'Scout Agent',   desc: 'Profiles every column – dtype, nulls, top values, ID detection' },
          { emoji: '🧠', label: 'Planner Agent', desc: 'LLM designs 5–6 business-critical chart specs' },
          { emoji: '🔍', label: 'Critic Agent',  desc: 'Validates specs, auto-repairs bad columns & aggregations' },
          { emoji: '⚙️', label: 'Builder Agent', desc: 'Executes specs, skips empties, returns clean chart data' },
        ].map((item, i) => (
          <div className="pipeline-m3-pill" key={i}>
            <span className="pipeline-m3-emoji">{item.emoji}</span>
            <div>
              <span className="pipeline-m3-label">{item.label}</span>
              <span className="pipeline-m3-desc">{item.desc}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="pipeline-flow">
        {steps.map((step, i) => {
          const config = statusConfig[step.status] || statusConfig.success;
          const StatusIcon = config.icon;
          const nameInfo = stepNameMap[step.step] || { label: step.step.replace(/_/g, ' '), emoji: '🔧' };

          return (
            <motion.div
              key={i}
              className="pipeline-step-row"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.08, duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
            >
              {/* Connector */}
              <div className="step-connector">
                <div className="connector-line-top" style={{ opacity: i === 0 ? 0 : 1 }} />
                <div className="connector-dot" style={{ borderColor: config.color, background: config.bg }}>
                  <StatusIcon size={14} color={config.color} />
                </div>
                <div className="connector-line-bottom" style={{ opacity: i === steps.length - 1 ? 0 : 1 }} />
              </div>

              {/* Card */}
              <div className="step-card glass-card" style={{ borderLeftColor: config.color }}>
                <div className="step-card-header">
                  <div className="step-card-title">
                    <span className="step-emoji">{nameInfo.emoji}</span>
                    <div>
                      <h4>{nameInfo.label}</h4>
                      <span className="step-name-raw">{step.step}</span>
                    </div>
                  </div>
                  <span className="step-status-badge" style={{ color: config.color, background: config.bg }}>
                    {config.label}
                  </span>
                </div>
                {step.details && (
                  <pre className="step-details-text">{step.details}</pre>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>

      <style>{`
        .pipeline-view {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .pipeline-empty {
          padding: 60px 40px;
          text-align: center;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 12px;
          color: var(--text-dim);
        }

        .pipeline-summary {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 16px 20px;
          border-radius: var(--radius-lg);
        }

        .pipeline-summary-left {
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .pipeline-title {
          font-weight: 600;
          font-size: 15px;
          color: var(--text);
        }

        .pipeline-summary-stats {
          display: flex;
          gap: 8px;
        }

        .stat-pill {
          padding: 4px 12px;
          border-radius: var(--radius-full);
          font-size: 12px;
          font-weight: 600;
          font-family: var(--font-mono);
        }

        .success-pill {
          background: rgba(16, 185, 129, 0.1);
          color: #10b981;
        }

        .fail-pill {
          background: rgba(239, 68, 68, 0.1);
          color: #ef4444;
        }

        .total-pill {
          background: rgba(99, 102, 241, 0.1);
          color: #6366f1;
        }

        .pipeline-module3-pills {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 10px;
          margin-bottom: 4px;
        }

        .pipeline-m3-pill {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 10px 14px;
          border: 1px solid rgba(99, 102, 241, 0.12);
          border-radius: var(--radius-md);
          background: rgba(99, 102, 241, 0.04);
        }

        .pipeline-m3-emoji {
          font-size: 18px;
          line-height: 1;
          flex-shrink: 0;
        }

        .pipeline-m3-pill div {
          display: flex;
          flex-direction: column;
          gap: 1px;
        }

        .pipeline-m3-label {
          font-size: 12px;
          font-weight: 600;
          color: var(--text);
        }

        .pipeline-m3-desc {
          font-size: 11px;
          color: var(--text-dim);
        }

        .pipeline-flow {
          display: flex;
          flex-direction: column;
        }


        .pipeline-step-row {
          display: flex;
          gap: 16px;
        }

        .step-connector {
          display: flex;
          flex-direction: column;
          align-items: center;
          width: 32px;
          flex-shrink: 0;
        }

        .connector-line-top,
        .connector-line-bottom {
          width: 2px;
          flex: 1;
          background: rgba(255, 255, 255, 0.06);
        }

        .connector-dot {
          width: 28px;
          height: 28px;
          border-radius: 50%;
          border: 2px solid;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }

        .step-card {
          flex: 1;
          padding: 16px 20px;
          margin-bottom: 8px;
          border-left: 3px solid;
          border-radius: var(--radius-md);
        }

        .step-card-header {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: 12px;
        }

        .step-card-title {
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .step-emoji {
          font-size: 20px;
          line-height: 1;
        }

        .step-card-title h4 {
          font-size: 14px;
          font-weight: 600;
          color: var(--text);
          margin-bottom: 2px;
        }

        .step-name-raw {
          font-size: 11px;
          color: var(--text-muted);
          font-family: var(--font-mono);
        }

        .step-status-badge {
          padding: 4px 10px;
          border-radius: var(--radius-full);
          font-size: 11px;
          font-weight: 600;
          white-space: nowrap;
        }

        .step-details-text {
          margin-top: 12px;
          padding: 12px 16px;
          background: rgba(0, 0, 0, 0.2);
          border-radius: var(--radius-sm);
          font-family: var(--font-mono);
          font-size: 12px;
          color: var(--text-dim);
          line-height: 1.6;
          white-space: pre-wrap;
          word-break: break-word;
          max-height: 150px;
          overflow-y: auto;
          border: 1px solid rgba(255, 255, 255, 0.03);
        }
      `}</style>
    </div>
  );
};

export default PipelineView;
