import React, { useState, useRef, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, Legend
} from 'recharts';
import {
  Brain,
  Send,
  Loader2,
  MessageSquare,
  BarChart3,
  Lightbulb,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  AlertTriangle
} from 'lucide-react';

const BACKEND_URL = 'http://127.0.0.1:8000/api';

const CHART_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4'];

const AnalystView = ({ datasetId, module1Data }) => {
  // Analysis State
  const [analysisQuery, setAnalysisQuery] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [analysisError, setAnalysisError] = useState('');

  // Chat State
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [isChatting, setIsChatting] = useState(false);
  const chatScrollRef = useRef(null);

  // Auto-run analysis on mount
  useEffect(() => {
    if (datasetId && !analysisResult && !isAnalyzing) {
      handleAnalyze();
    }
  }, [datasetId]);

  // Auto-scroll chat
  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight;
    }
  }, [chatMessages]);

  const renderedCharts = useMemo(() => {
    if (!analysisResult?.charts || analysisResult.charts.length === 0) return null;
    return (
      <div className="charts-grid">
        {analysisResult.charts.map((chart, idx) => (
          <div key={idx} className="glass-card chart-wrapper">
            <h4>{chart.title}</h4>
            <div className="chart-render-area">
              {chart.figure && chart.figure.data && chart.figure.data[0] ? (
                (() => {
                  const pData = chart.figure.data[0];
                  const chartType = pData.type;
                  const isHorizontal = chartType === 'horizontal_bar';
                  const dataPoints = (pData.x || []).map((xVal, i) => ({
                    name: String(xVal).length > 15 ? String(xVal).substring(0, 15) + '...' : xVal,
                    value: pData.y ? pData.y[i] : 0
                  }));
                  
                  const color = CHART_COLORS[idx % CHART_COLORS.length];
                  
                  return (
                    <ResponsiveContainer width="100%" height="100%">
                      {chartType === 'line' ? (
                        <LineChart data={dataPoints} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                          <XAxis dataKey="name" stroke="var(--text-muted)" tick={{ fontSize: 11 }} angle={-45} textAnchor="end" />
                          <YAxis stroke="var(--text-muted)" tick={{ fontSize: 11 }} />
                          <Tooltip
                            contentStyle={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                            itemStyle={{ color: '#f1f5f9' }}
                          />
                          <Line type="monotone" dataKey="value" stroke={color} strokeWidth={3} dot={{ r: 4, fill: color, strokeWidth: 2, stroke: '#1e293b' }} activeDot={{ r: 6 }} />
                        </LineChart>
                      ) : (
                        <BarChart data={dataPoints} layout={isHorizontal ? 'vertical' : 'horizontal'} margin={{ top: 10, right: 20, left: isHorizontal ? 40 : 0, bottom: 20 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={!isHorizontal} vertical={isHorizontal} />
                          <XAxis 
                            type={isHorizontal ? "number" : "category"} 
                            dataKey={isHorizontal ? undefined : "name"} 
                            stroke="var(--text-muted)" 
                            tick={{ fontSize: 11 }} 
                            angle={isHorizontal ? 0 : -45} 
                            textAnchor={isHorizontal ? "middle" : "end"} 
                          />
                          <YAxis 
                            type={isHorizontal ? "category" : "number"} 
                            dataKey={isHorizontal ? "name" : undefined} 
                            stroke="var(--text-muted)" 
                            tick={{ fontSize: 11 }} 
                            width={isHorizontal ? 80 : 40}
                          />
                          <Tooltip
                            contentStyle={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                            itemStyle={{ color: '#f1f5f9' }}
                            cursor={{ fill: 'rgba(255,255,255,0.03)' }}
                          />
                          <Bar dataKey="value" fill={color} radius={isHorizontal ? [0, 4, 4, 0] : [4, 4, 0, 0]}>
                            {dataPoints.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={CHART_COLORS[(idx + index) % CHART_COLORS.length]} />
                            ))}
                          </Bar>
                        </BarChart>
                      )}
                    </ResponsiveContainer>
                  );
                })()
              ) : (
                <div className="no-chart-data">Chart data unavailable</div>
              )}
            </div>
          </div>
        ))}
      </div>
    );
  }, [analysisResult?.charts]);

  const handleAnalyze = async (e) => {
    if (e) e.preventDefault();
    
    if (!datasetId) {
      setAnalysisError("Session expired or dataset missing. Please click 'New Dataset' and re-upload your file.");
      return;
    }

    setIsAnalyzing(true);
    setAnalysisError('');
    try {
      const response = await axios.post(`${BACKEND_URL}/analyze`, {
        dataset_id: datasetId,
        query: "Generate a complete data summary dashboard including main trends and comparisons."
      });
      setAnalysisResult(response.data);
      // Auto-add an initial assistant message based on analysis
      if (chatMessages.length === 0) {
        setChatMessages([
          { role: 'assistant', text: "I've generated your report! Feel free to ask any follow-up questions here." }
        ]);
      }
    } catch (err) {
      console.error(err);
      setAnalysisError(err.response?.data?.detail || "Failed to analyze dataset.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleChat = async (e) => {
    e?.preventDefault();
    if (!chatInput.trim() || isChatting) return;

    if (!datasetId) {
      setChatMessages(prev => [...prev, { role: 'assistant', text: "⚠️ Please click 'New Dataset' and re-upload your file to start chatting." }]);
      return;
    }

    const userMessage = chatInput;
    setChatInput('');
    setChatMessages(prev => [...prev, { role: 'user', text: userMessage }]);
    setIsChatting(true);

    try {
      const history = chatMessages.map(m => ({ role: m.role, content: m.text }));
      const response = await axios.post(`${BACKEND_URL}/chat`, {
        dataset_id: datasetId,
        query: userMessage,
        history: history
      });

      setChatMessages(prev => [...prev, { role: 'assistant', text: response.data.answer }]);
    } catch (err) {
      console.error(err);
      setChatMessages(prev => [...prev, { role: 'assistant', text: "⚠️ Sorry, I encountered an error answering your question." }]);
    } finally {
      setIsChatting(false);
    }
  };

  return (
    <div className="analyst-view-container">
      {/* ─── LEFT PANEL: Analysis & Charts ─── */}
      <div className="analysis-panel">
        <div className="panel-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div className="header-title">
              <Brain size={20} color="var(--primary)" />
              <h2>AI Data Analyst</h2>
            </div>
            <p>Comprehensive statistical report and charts, automatically generated by AI.</p>
          </div>
          
          <button 
            onClick={() => handleAnalyze()} 
            disabled={isAnalyzing}
            style={{
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.1)',
              padding: '6px 12px',
              borderRadius: '6px',
              color: 'var(--text)',
              cursor: isAnalyzing ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '13px'
            }}
          >
            {isAnalyzing ? <Loader2 size={14} className="animate-spin" /> : <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/><path d="M16 21v-5h5"/></svg>}
            Refresh
          </button>
        </div>

        {analysisError && (
          <div className="error-toast" style={{ marginTop: '16px' }}>
            <AlertTriangle size={16} /> {analysisError}
          </div>
        )}

        <div className="analysis-results-scroll">
          {isAnalyzing && (
            <div className="loading-state">
              <div className="loader-spinner-ring" style={{ width: 60, height: 60 }}>
                <Loader2 size={32} className="animate-spin" color="var(--primary)" />
              </div>
              <p>Orchestrating multi-agent analysis...</p>
              <p className="loading-sub">Building RAG context, running statistical tests, and rendering charts.</p>
            </div>
          )}

          <AnimatePresence>
            {!isAnalyzing && analysisResult && (
              <motion.div
                className="results-content"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
              >
                {/* Insights Summary */}
                <div className="glass-card result-section">
                  <div className="section-header">
                    <Lightbulb size={18} color="#f59e0b" />
                    <h3>Key Insights</h3>
                  </div>
                  <div className="insights-list">
                    {analysisResult.insights?.map((insight, idx) => (
                      <div key={idx} className="insight-item">
                        <CheckCircle2 size={16} color="#10b981" className="shrink-0 mt-1" />
                        <p>{insight}</p>
                      </div>
                    ))}
                  </div>
                  {analysisResult.explanations && (
                    <div className="explanation-box">
                      <strong>AI Explanation:</strong> {analysisResult.explanations}
                    </div>
                  )}
                  {analysisResult.confidence_score && (
                    <div className="confidence-badge">
                      Confidence Score: {(analysisResult.confidence_score * 100).toFixed(1)}%
                    </div>
                  )}
                </div>

                {/* Analysis Plan */}
                {analysisResult.analysis_plan && analysisResult.analysis_plan.length > 0 && (
                  <div className="glass-card result-section">
                    <div className="section-header">
                      <Brain size={18} color="var(--cyan)" />
                      <h3>Execution Plan</h3>
                    </div>
                    <div className="plan-steps">
                      {analysisResult.analysis_plan.map((step, idx) => (
                        <div key={idx} className="plan-step">
                          <span className="step-num">{idx + 1}</span>
                          <span>{step}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Charts Grid */}
                {renderedCharts}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* ─── RIGHT PANEL: Chatbot ─── */}
      <div className="chat-panel glass-card">
        <div className="chat-header">
          <MessageSquare size={18} color="var(--primary)" />
          <h3>Interactive Q&A</h3>
        </div>
        
        <div className="chat-messages" ref={chatScrollRef}>
          {chatMessages.length === 0 ? (
            <div className="chat-empty">
              <Brain size={32} color="rgba(255,255,255,0.1)" />
              <p>Ask anything about your dataset.<br/>I have full access to the data, schema, and analysis results.</p>
            </div>
          ) : (
            chatMessages.map((msg, idx) => (
              <div key={idx} className={`chat-bubble ${msg.role}`}>
                <div className="bubble-content">{msg.text}</div>
              </div>
            ))
          )}
          {isChatting && (
            <div className="chat-bubble assistant typing">
              <div className="typing-dots">
                <span></span><span></span><span></span>
              </div>
            </div>
          )}
        </div>

        <form onSubmit={handleChat} className="chat-input-area">
          <input
            type="text"
            placeholder="Type your question..."
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            disabled={isChatting || !datasetId}
          />
          <button type="submit" disabled={isChatting || !chatInput.trim()} className="send-btn">
            <Send size={16} />
          </button>
        </form>
      </div>

      <style>{`
        .analyst-view-container {
          display: flex;
          gap: 20px;
          height: calc(100vh - 140px);
          overflow: hidden;
        }

        .analysis-panel {
          flex: 2;
          display: flex;
          flex-direction: column;
          gap: 16px;
          overflow: hidden;
        }

        .panel-header {
          flex-shrink: 0;
        }

        .header-title {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 6px;
        }

        .header-title h2 {
          font-size: 20px;
          font-weight: 600;
        }

        .panel-header p {
          color: var(--text-dim);
          font-size: 14px;
        }

        .analysis-input-form {
          display: flex;
          gap: 12px;
          padding: 12px;
          flex-shrink: 0;
        }

        .analysis-input-form input {
          flex: 1;
          background: rgba(0,0,0,0.2);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: var(--radius-md);
          padding: 10px 16px;
          color: var(--text);
          font-size: 14px;
          outline: none;
          transition: border-color 0.2s;
        }

        .analysis-input-form input:focus {
          border-color: var(--primary);
        }

        .analysis-results-scroll {
          flex: 1;
          overflow-y: auto;
          padding-right: 8px;
          padding-bottom: 20px;
        }

        .analysis-results-scroll::-webkit-scrollbar {
          width: 6px;
        }
        .analysis-results-scroll::-webkit-scrollbar-thumb {
          background: rgba(255,255,255,0.1);
          border-radius: 10px;
        }

        .loading-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 100%;
          gap: 16px;
          color: var(--text-dim);
        }

        .loading-sub {
          font-size: 13px;
          color: var(--text-muted);
        }

        .results-content {
          display: flex;
          flex-direction: column;
          gap: 20px;
        }

        .result-section {
          padding: 20px;
        }

        .section-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 16px;
          border-bottom: 1px solid rgba(255,255,255,0.05);
          padding-bottom: 12px;
        }

        .section-header h3 {
          font-size: 16px;
          font-weight: 600;
        }

        .insights-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .insight-item {
          display: flex;
          align-items: flex-start;
          gap: 10px;
          background: rgba(16, 185, 129, 0.05);
          padding: 12px;
          border-radius: var(--radius-md);
          border: 1px solid rgba(16, 185, 129, 0.1);
          font-size: 14px;
          line-height: 1.5;
        }

        .explanation-box {
          margin-top: 16px;
          padding: 16px;
          background: rgba(255,255,255,0.03);
          border-radius: var(--radius-md);
          font-size: 14px;
          line-height: 1.6;
          color: var(--text-dim);
        }

        .confidence-badge {
          margin-top: 16px;
          display: inline-block;
          background: rgba(99, 102, 241, 0.1);
          color: var(--primary);
          padding: 6px 12px;
          border-radius: var(--radius-full);
          font-size: 12px;
          font-weight: 600;
        }

        .plan-steps {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        .plan-step {
          display: flex;
          align-items: center;
          gap: 12px;
          font-size: 14px;
          color: var(--text-dim);
        }

        .step-num {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 24px;
          height: 24px;
          border-radius: 50%;
          background: rgba(255,255,255,0.05);
          color: var(--text);
          font-size: 12px;
          font-weight: 600;
        }

        .charts-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
          gap: 20px;
        }

        .chart-wrapper {
          padding: 20px;
          display: flex;
          flex-direction: column;
          background: rgba(15, 23, 42, 0.4);
          border: 1px solid rgba(255,255,255,0.05);
          border-radius: var(--radius-lg);
          transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .chart-wrapper:hover {
          transform: translateY(-2px);
          box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
          border-color: rgba(255,255,255,0.1);
        }

        .chart-wrapper h4 {
          font-size: 14px;
          font-weight: 600;
          margin-bottom: 12px;
          text-align: center;
          color: var(--text-dim);
        }

        .chart-render-area {
          height: 300px;
          width: 100%;
          position: relative;
        }

        /* ─── CHAT PANEL ─── */
        .chat-panel {
          flex: 1;
          min-width: 320px;
          max-width: 400px;
          display: flex;
          flex-direction: column;
          border-radius: var(--radius-lg);
          overflow: hidden;
        }

        .chat-header {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 16px 20px;
          background: rgba(255,255,255,0.02);
          border-bottom: 1px solid var(--glass-border);
        }

        .chat-header h3 {
          font-size: 15px;
          font-weight: 600;
        }

        .chat-messages {
          flex: 1;
          overflow-y: auto;
          padding: 20px;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .chat-empty {
          height: 100%;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 16px;
          text-align: center;
          color: var(--text-muted);
          font-size: 13px;
        }

        .chat-bubble {
          max-width: 85%;
          display: flex;
          flex-direction: column;
        }

        .chat-bubble.user {
          align-self: flex-end;
        }

        .chat-bubble.assistant {
          align-self: flex-start;
        }

        .bubble-content {
          padding: 12px 16px;
          border-radius: 16px;
          font-size: 14px;
          line-height: 1.5;
        }

        .chat-bubble.user .bubble-content {
          background: var(--primary);
          color: white;
          border-bottom-right-radius: 4px;
        }

        .chat-bubble.assistant .bubble-content {
          background: rgba(255,255,255,0.05);
          border: 1px solid rgba(255,255,255,0.1);
          color: var(--text);
          border-bottom-left-radius: 4px;
        }

        .chat-input-area {
          padding: 16px;
          border-top: 1px solid var(--glass-border);
          display: flex;
          gap: 8px;
        }

        .chat-input-area input {
          flex: 1;
          background: rgba(0,0,0,0.2);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 20px;
          padding: 10px 16px;
          color: var(--text);
          font-size: 14px;
          outline: none;
        }

        .chat-input-area input:focus {
          border-color: var(--primary);
        }

        .send-btn {
          width: 40px;
          height: 40px;
          border-radius: 50%;
          background: var(--primary);
          color: white;
          border: none;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all 0.2s;
        }

        .send-btn:hover:not(:disabled) {
          background: var(--accent);
        }

        .send-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .typing-dots {
          display: flex;
          gap: 4px;
          padding: 16px;
          background: rgba(255,255,255,0.05);
          border-radius: 16px;
          border-bottom-left-radius: 4px;
        }

        .typing-dots span {
          width: 6px;
          height: 6px;
          background: var(--text-muted);
          border-radius: 50%;
          animation: typing 1.4s infinite ease-in-out;
        }

        .typing-dots span:nth-child(1) { animation-delay: 0s; }
        .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
        .typing-dots span:nth-child(3) { animation-delay: 0.4s; }

        @keyframes typing {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-4px); }
        }
      `}</style>
    </div>
  );
};

export default AnalystView;
