import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import UploadZone from './components/UploadZone';
import Dashboard from './components/Dashboard';
import { Loader2, Database, Brain, Sparkles, ShieldCheck, Layers, Target, TrendingUp } from 'lucide-react';

import { API_URL as BASE_API_URL } from './apiConfig';

const API_URL = `${BASE_API_URL}/process`;

const pipelinePhases = [
  { icon: Brain, label: 'Understanding your data...', detail: 'AI analyzing schema, domains, and column meanings' },
  { icon: Database, label: 'Running deep EDA...', detail: 'Detecting outliers, correlations, and quality issues' },
  { icon: Sparkles, label: 'AI planning pipeline...', detail: 'Choosing optimal cleaning & encoding strategy' },
  { icon: Layers, label: 'Executing pipeline...', detail: 'Imputing, encoding, scaling — building ML-ready dataset' },
  { icon: ShieldCheck, label: 'Assembling results...', detail: 'Packaging datasets, artifacts, and quality report' },
  { icon: Target, label: 'AI Analyst Generation (Mod 3)...', detail: 'Extracting strategic insights and natural language reports' },
  { icon: TrendingUp, label: 'Decision Intelligence Prep (Mod 4)...', detail: 'Readying AutoML predictive pipelines and RCA structures' },
];

function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [phaseIndex, setPhaseIndex] = useState(0);

  useEffect(() => {
    if (!loading) return;
    setPhaseIndex(0);
    const interval = setInterval(() => {
      setPhaseIndex(prev => {
        if (prev < pipelinePhases.length - 1) return prev + 1;
        return prev;
      });
    }, 3500);
    return () => clearInterval(interval);
  }, [loading]);

  const handleUpload = async (file) => {
    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('target_column', '');

    try {
      const response = await axios.post(API_URL, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setData(response.data);
    } catch (err) {
      console.error("Backend Error:", err);
      setError(err.response?.data?.detail || "Connection to AI Engine failed. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setData(null);
    setError(null);
  };

  return (
    <div className="app-wrapper">
      <div className="bg-gradient" />

      <AnimatePresence mode="wait">
        {/* ─── HERO / UPLOAD ─── */}
        {!data && !loading && (
          <motion.div
            key="hero"
            className="hero-section"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, y: -30 }}
            transition={{ duration: 0.4 }}
          >
            <div className="hero-content">
              <motion.div
                className="badge"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.2 }}
              >
                <Database size={13} strokeWidth={1.5} /> AI-Powered Data Intelligence
              </motion.div>

              <motion.h1
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
              >
                <span>AI Career Companion </span>
              </motion.h1>

              <motion.p
                className="hero-desc"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
              >
                Upload any dataset. Our AI agent will analyze, clean, encode, and scale your data — producing ML-ready outputs with a full quality report in seconds.
              </motion.p>

              <motion.div
                className="upload-wrapper"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
              >
                <UploadZone onUpload={handleUpload} />
              </motion.div>

              {error && (
                <motion.div
                  className="error-toast"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  ⚠️ {error}
                </motion.div>
              )}
            </div>
          </motion.div>
        )}

        {/* ─── LOADING / PIPELINE PROGRESS ─── */}
        {loading && (
          <motion.div
            key="loading"
            className="loading-screen"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <div className="loader-card glass-card">
              <div className="loader-spinner-ring">
                <Loader2 className="spinner-icon" size={40} strokeWidth={1.5} />
              </div>

              <AnimatePresence mode="wait">
                <motion.div
                  key={phaseIndex}
                  className="phase-info"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -12 }}
                  transition={{ duration: 0.3 }}
                >
                  {(() => {
                    const Phase = pipelinePhases[phaseIndex];
                    return (
                      <>
                        <h2>{Phase.label}</h2>
                        <p>{Phase.detail}</p>
                      </>
                    );
                  })()}
                </motion.div>
              </AnimatePresence>

              {/* Phase dots */}
              <div className="phase-steps">
                {pipelinePhases.map((p, i) => {
                  const PhaseIcon = p.icon;
                  return (
                    <div
                      key={i}
                      className={`phase-dot ${i < phaseIndex ? 'done' : i === phaseIndex ? 'active' : ''}`}
                    >
                      <PhaseIcon size={14} strokeWidth={1.5} />
                    </div>
                  );
                })}
              </div>

              <div className="progress-bar">
                <motion.div
                  className="progress-fill"
                  initial={{ width: '0%' }}
                  animate={{ width: `${((phaseIndex + 1) / pipelinePhases.length) * 100}%` }}
                  transition={{ duration: 0.8, ease: 'easeOut' }}
                />
              </div>
            </div>
          </motion.div>
        )}

        {/* ─── DASHBOARD ─── */}
        {data && (
          <motion.div
            key="dashboard"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="dashboard-wrapper"
          >
            <Dashboard data={data} onReset={handleReset} />
          </motion.div>
        )}
      </AnimatePresence>

      <style>{`
        .app-wrapper {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          color: var(--text);
        }

        /* ─── Hero ─── */
        .hero-section {
          width: 100%;
          max-width: 900px;
          padding: 40px 24px;
          text-align: center;
        }

        .hero-content {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 16px;
        }

        .badge {
          background: rgba(99, 102, 241, 0.08);
          border: 1px solid rgba(99, 102, 241, 0.15);
          color: var(--primary);
          padding: 6px 16px;
          border-radius: var(--radius-full);
          font-size: 13px;
          font-weight: 600;
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .hero-content h1 {
          font-size: 56px;
          font-weight: 800;
          letter-spacing: -2px;
          line-height: 1.1;
        }

        .hero-content h1 span {
          background: linear-gradient(135deg, var(--primary), var(--secondary));
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }

        .hero-desc {
          color: var(--text-dim);
          font-size: 16px;
          max-width: 600px;
          line-height: 1.6;
        }

        .upload-wrapper {
          margin-top: 20px;
          width: 100%;
        }

        .error-toast {
          background: rgba(239, 68, 68, 0.1);
          border: 1px solid rgba(239, 68, 68, 0.2);
          color: #ff8a8a;
          padding: 12px 24px;
          border-radius: var(--radius-md);
          font-size: 14px;
          margin-top: 8px;
          max-width: 600px;
        }

        /* ─── Loading ─── */
        .loading-screen {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 100%;
          padding: 40px;
        }

        .loader-card {
          text-align: center;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 24px;
          padding: 48px 56px;
          border-radius: var(--radius-xl);
          min-width: 420px;
        }

        .loader-spinner-ring {
          width: 72px;
          height: 72px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          background: radial-gradient(circle, rgba(99, 102, 241, 0.08), transparent);
        }

        .spinner-icon {
          animation: spin 1.2s linear infinite;
          color: var(--primary);
        }

        .phase-info {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 6px;
        }

        .phase-info h2 {
          font-size: 18px;
          font-weight: 600;
        }

        .phase-info p {
          font-size: 13px;
          color: var(--text-dim);
        }

        .phase-steps {
          display: flex;
          gap: 10px;
        }

        .phase-dot {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.06);
          color: var(--text-muted);
          transition: all 0.3s ease;
        }

        .phase-dot.active {
          background: rgba(99, 102, 241, 0.15);
          border-color: rgba(99, 102, 241, 0.4);
          color: var(--primary);
          animation: float 2s ease-in-out infinite;
        }

        .phase-dot.done {
          background: rgba(16, 185, 129, 0.12);
          border-color: rgba(16, 185, 129, 0.3);
          color: #10b981;
        }

        .progress-bar {
          width: 100%;
          height: 4px;
          background: rgba(255, 255, 255, 0.06);
          border-radius: 10px;
          overflow: hidden;
        }

        .progress-fill {
          height: 100%;
          background: linear-gradient(90deg, var(--primary), var(--accent));
          border-radius: 10px;
        }

        /* ─── Dashboard ─── */
        .dashboard-wrapper {
          width: 100%;
          height: 100vh;
        }

        @media (max-width: 640px) {
          .hero-content h1 {
            font-size: 36px;
          }
        }
      `}</style>
    </div>
  );
}

export default App;
