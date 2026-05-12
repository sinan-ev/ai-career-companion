import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, FileText, X, Zap, Database, Shield, Brain, BarChart3, Target, TrendingUp } from 'lucide-react';

const UploadZone = ({ onUpload }) => {
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState(null);
  const inputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      const ext = droppedFile.name.split('.').pop().toLowerCase();
      if (['csv', 'xlsx', 'xls'].includes(ext)) {
        setFile(droppedFile);
      } else {
        alert("Please upload a CSV or Excel file");
      }
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const clearFile = () => {
    setFile(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  const handleSubmit = () => {
    if (file) onUpload(file);
  };

  const features = [
    { icon: Brain, label: "Mod 1: AI Understanding", desc: "Schema, cleaning, quality" },
    { icon: Database, label: "Mod 2: Data Engineering", desc: "Auto ML-ready datasets" },
    { icon: BarChart3, label: "Mod 3A: AI Analyst", desc: "Chat, Dashboards & Insights" },
    { icon: TrendingUp, label: "Mod 3B: Decision Intel", desc: "Predictions, Forecasts & RCA" },
  ];

  return (
    <div className="upload-container">
      <motion.div 
        className={`upload-zone ${dragActive ? 'drag-active' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      >
        <input 
          ref={inputRef}
          type="file" 
          id="input-file-upload" 
          multiple={false} 
          accept=".csv,.xlsx,.xls"
          onChange={handleChange} 
          style={{ display: 'none' }}
        />
        
        <AnimatePresence mode="wait">
          {!file ? (
            <motion.label 
              key="empty"
              htmlFor="input-file-upload"
              className="upload-label"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              <div className="upload-icon-wrapper">
                <div className="upload-icon-ring" />
                <div className="upload-icon-bg">
                  <Upload size={36} strokeWidth={1.5} />
                </div>
              </div>
              <h3>Drop your dataset here</h3>
              <p>or click to browse files</p>
              <div className="file-types">
                <span className="file-chip">.CSV</span>
                <span className="file-chip">.XLSX</span>
                <span className="file-chip">.XLS</span>
              </div>
            </motion.label>
          ) : (
            <motion.div 
              key="selected"
              className="file-preview"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
            >
              <div className="file-info-container">
                <div className="file-icon-bg">
                  <FileText size={28} strokeWidth={1.5} />
                </div>
                <div className="file-details">
                  <span className="file-name">{file.name}</span>
                  <span className="file-size">{(file.size / 1024).toFixed(1)} KB • Ready</span>
                </div>
                <button className="clear-btn" onClick={clearFile}>
                  <X size={16} />
                </button>
              </div>
              
              <motion.button 
                className="launch-btn"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleSubmit}
              >
                <Zap size={20} />
                <span>Launch Pipeline</span>
                <div className="launch-btn-shimmer" />
              </motion.button>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>


      <motion.div 
        className="features-row"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
      >
        {features.map((f, i) => (
          <div className="feature-pill" key={i}>
            <f.icon size={16} strokeWidth={1.5} />
            <div>
              <span className="feature-label">{f.label}</span>
              <span className="feature-desc">{f.desc}</span>
            </div>
          </div>
        ))}
      </motion.div>

      <style>{`
        .upload-container {
          width: 100%;
          max-width: 640px;
          margin: 0 auto;
          display: flex;
          flex-direction: column;
          gap: 28px;
        }

        .upload-zone {
          position: relative;
          padding: 56px 40px;
          text-align: center;
          border: 1.5px dashed rgba(99, 102, 241, 0.2);
          border-radius: var(--radius-xl);
          background: rgba(17, 24, 39, 0.5);
          backdrop-filter: blur(12px);
          transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
          overflow: hidden;
        }

        .upload-zone::before {
          content: '';
          position: absolute;
          inset: 0;
          border-radius: inherit;
          background: radial-gradient(circle at 50% 50%, rgba(99, 102, 241, 0.04), transparent 70%);
          pointer-events: none;
        }

        .drag-active {
          border-color: var(--primary);
          background: rgba(99, 102, 241, 0.08);
          transform: scale(1.01);
          box-shadow: 0 0 40px rgba(99, 102, 241, 0.15);
        }

        .upload-label {
          cursor: pointer;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 14px;
        }

        .upload-icon-wrapper {
          position: relative;
          margin-bottom: 8px;
        }

        .upload-icon-ring {
          position: absolute;
          inset: -6px;
          border-radius: 50%;
          border: 1.5px solid rgba(99, 102, 241, 0.2);
          animation: pulse-ring 2.5s ease-out infinite;
        }

        .upload-icon-bg {
          width: 72px;
          height: 72px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(139, 92, 246, 0.1));
          color: var(--primary);
        }

        .upload-label h3 {
          font-size: 20px;
          font-weight: 600;
          color: var(--text);
          letter-spacing: -0.3px;
        }

        .upload-label p {
          color: var(--text-dim);
          font-size: 15px;
        }

        .file-types {
          display: flex;
          gap: 8px;
          margin-top: 4px;
        }

        .file-chip {
          background: rgba(255, 255, 255, 0.04);
          border: 1px solid rgba(255, 255, 255, 0.06);
          padding: 4px 12px;
          border-radius: var(--radius-full);
          font-size: 11px;
          font-weight: 600;
          color: var(--text-dim);
          font-family: var(--font-mono);
          letter-spacing: 0.5px;
        }

        .file-preview {
          display: flex;
          flex-direction: column;
          align-items: stretch;
          gap: 20px;
        }

        .file-info-container {
          display: flex;
          align-items: center;
          gap: 14px;
          padding: 14px 16px;
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.06);
          border-radius: var(--radius-lg);
        }

        .file-icon-bg {
          width: 48px;
          height: 48px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(135deg, rgba(99, 102, 241, 0.12), rgba(139, 92, 246, 0.08));
          border-radius: var(--radius-md);
          color: var(--primary);
          flex-shrink: 0;
        }

        .file-details {
          flex: 1;
          text-align: left;
          display: flex;
          flex-direction: column;
          gap: 2px;
        }

        .file-name {
          font-weight: 600;
          color: var(--text);
          font-size: 15px;
          max-width: 260px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .file-size {
          font-size: 13px;
          color: var(--success);
          font-weight: 500;
        }

        .clear-btn {
          background: none;
          border: 1px solid rgba(255, 255, 255, 0.06);
          color: var(--text-dim);
          cursor: pointer;
          width: 32px;
          height: 32px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all var(--transition-fast);
          flex-shrink: 0;
        }

        .clear-btn:hover {
          background: var(--error-bg);
          border-color: rgba(239, 68, 68, 0.2);
          color: var(--error);
        }

        .launch-btn {
          position: relative;
          width: 100%;
          padding: 14px 24px;
          background: linear-gradient(135deg, var(--primary), var(--accent));
          border: none;
          border-radius: var(--radius-md);
          color: white;
          font-size: 16px;
          font-weight: 600;
          font-family: inherit;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 10px;
          overflow: hidden;
          transition: box-shadow var(--transition-base);
        }

        .launch-btn:hover {
          box-shadow: 0 6px 30px var(--primary-glow);
        }

        .launch-btn-shimmer {
          position: absolute;
          inset: 0;
          background: linear-gradient(
            90deg,
            transparent 0%,
            rgba(255,255,255,0.12) 50%,
            transparent 100%
          );
          background-size: 200% 100%;
          animation: shimmer 2s linear infinite;
        }

        .features-row {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 12px;
        }

        .feature-pill {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 12px 14px;
          border: 1px solid rgba(255, 255, 255, 0.05);
          border-radius: var(--radius-md);
          background: rgba(255, 255, 255, 0.02);
          color: var(--primary);
        }

        .feature-pill div {
          display: flex;
          flex-direction: column;
        }

        .feature-label {
          font-size: 13px;
          font-weight: 600;
          color: var(--text);
        }

        .feature-desc {
          font-size: 11px;
          color: var(--text-dim);
        }

        @media (max-width: 640px) {
          .features-row {
            grid-template-columns: 1fr;
          }
          .upload-zone {
            padding: 40px 24px;
          }
        }
      `}</style>
    </div>
  );
};

export default UploadZone;
