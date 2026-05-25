import React, { useState } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Brain, Target, TrendingUp, AlertTriangle, CheckCircle, 
  Lightbulb, Activity, ArrowRight, ShieldCheck, Download, LineChart as LineChartIcon, Sparkles, MessageSquare, X, Send
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Cell,
  LineChart, Line, AreaChart, Area, Legend, ReferenceLine
} from 'recharts';

import { BACKEND_URL } from '../apiConfig';

const API_URL = `${BACKEND_URL}/api/4/run-pipeline`;

const DecisionIntelligenceView = ({ data, targetColumn, featureColumns, activeView }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState([
    { role: 'ai', text: 'Hello! I am your Future Intelligence Assistant. I can help explain the predicted datasets, business insights, and recommend strategic actions. What would you like to know?' }
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const chatBodyRef = React.useRef(null);

  React.useEffect(() => {
    if (chatBodyRef.current) {
      chatBodyRef.current.scrollTop = chatBodyRef.current.scrollHeight;
    }
  }, [chatMessages, isTyping]);

  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if(!chatInput.trim()) return;
    
    const message = chatInput;
    const userMsg = { role: 'user', text: message };
    setChatMessages(prev => [...prev, userMsg]);
    setChatInput('');
    setIsTyping(true);
    
    try {
      const response = await axios.post(`${BACKEND_URL}/api/4/chat`, {
        message: message,
        context: result || {}
      });
      setChatMessages(prev => [...prev, { role: 'ai', text: response.data.response }]);
    } catch (err) {
      console.error("Chat error:", err);
      setChatMessages(prev => [...prev, { role: 'ai', text: "Sorry, I'm having trouble connecting to the intelligence engine right now." }]);
    } finally {
      setIsTyping(false);
    }
  };
  
  const [currentTarget, setCurrentTarget] = useState(targetColumn);
  
  // Update internal target if props change
  React.useEffect(() => {
    if (targetColumn && targetColumn !== currentTarget) {
      setCurrentTarget(targetColumn);
    }
  }, [targetColumn]);

  const handleRunPipeline = async (forceTarget = null) => {
    const activeTarget = forceTarget || currentTarget || (featureColumns && featureColumns.length > 0 ? featureColumns[featureColumns.length - 1] : "");
    
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // Filter out noisy/unwanted columns
      const unwantedKeywords = ['name', 'address', 'phone', 'city', 'postal', 'zip', 'email', 'id', 'contact'];
      
      const filteredData = data.map(row => {
        const cleanRow = {};
        for (const [key, value] of Object.entries(row)) {
          if (key === activeTarget) {
            cleanRow[key] = value;
            continue;
          }
          const lowerKey = key.toLowerCase();
          const isUnwanted = unwantedKeywords.some(kw => lowerKey.includes(kw));
          if (!isUnwanted) cleanRow[key] = value;
        }
        return cleanRow;
      });

      // Auto-detect date column
      let dateColumn = "";
      if (data && data.length > 0) {
        const columns = Object.keys(data[0]);
        const dateKeywords = ['date', 'time', 'year', 'month', 'day', 'timestamp'];
        for (const col of columns) {
          if (dateKeywords.some(kw => col.toLowerCase().includes(kw))) {
            dateColumn = col;
            break;
          }
        }
      }

      const payload = {
        data: filteredData,
        target_column: activeTarget,
        date_column: dateColumn,
        problem: `Analyze the dataset, predict ${activeTarget}, find root causes, and provide strategic recommendations.`
      };

      const response = await axios.post(API_URL, payload);
      setResult(response.data);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail?.message || "Failed to run decision pipeline.");
    } finally {
      setLoading(false);
    }
  };

  const onTargetChange = (newTarget) => {
    setCurrentTarget(newTarget);
    handleRunPipeline(newTarget);
  };

  React.useEffect(() => {
    if (!result && !loading && !error && data) {
      handleRunPipeline();
    }
  }, [data]);

  const getConfidenceColor = (level) => {
    switch (level?.toLowerCase()) {
      case 'very high': return '#10b981';
      case 'high': return '#3b82f6';
      case 'moderate': return '#f59e0b';
      case 'low': return '#f97316';
      case 'uncertain': return '#ef4444';
      default: return '#64748b';
    }
  };

  const ConfidenceBadge = ({ confidence }) => {
    if (!confidence) return null;
    const color = getConfidenceColor(confidence.level);
    return (
      <div className="confidence-badge" style={{ borderColor: color, background: `${color}15` }}>
        <div className="confidence-score" style={{ color }}>{Math.round(confidence.score * 100)}%</div>
        <div className="confidence-info">
          <span className="confidence-level" style={{ color }}>{confidence.level} Confidence</span>
          <span className="confidence-desc">{confidence.explanation}</span>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="di-loading-state">
        <div className="di-loader-card glass-card">
          <div className="pulse-ring">
            <Brain size={48} color="var(--primary)" />
          </div>
          <h3>Running AI Decision Intelligence</h3>
          <p>Analyzing predictions, calculating risks, and generating strategic solutions...</p>
          <div className="di-progress-bar">
            <motion.div 
              className="di-progress-fill"
              initial={{ width: '0%' }}
              animate={{ width: '100%' }}
              transition={{ duration: 15, ease: "linear" }}
            />
          </div>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="di-setup-state">
        <div className="glass-card auto-run-card">
          <div className="di-header">
            <div className="icon-wrapper">
              <Sparkles size={28} color="var(--primary)" />
            </div>
            <h2>Ready for Decision Intelligence</h2>
            <p>The AI has analyzed your dataset schema and is ready to automatically run the full predictive and strategic pipeline.</p>
          </div>
          
          <div className="di-auto-config">
            <div className="config-item">
              <span className="config-label">Target Column</span>
              <span className="config-value highlight">{targetColumn || "Auto-detect"}</span>
            </div>
            <div className="config-item">
              <span className="config-label">Sample Size</span>
              <span className="config-value">{data?.length || 0} rows</span>
            </div>
            <div className="config-item">
              <span className="config-label">Pipeline Tasks</span>
              <span className="config-value">Predictions, Root Cause Analysis, Risk Detection, Strategies</span>
            </div>
          </div>
          
          {error && <div className="di-error">⚠️ {error}</div>}
          
          <button className="di-run-btn" onClick={handleRunPipeline}>
            <Brain size={18} /> Initialize AI Pipeline
          </button>
        </div>
      </div>
    );
  }

  const { prediction, forecast, rca, risk, recommendation, decision, overall_confidence, final_report } = result;

  // Build a yearly sales trend from raw data
  const buildYearlySalesTrend = () => {
    if (!data || data.length === 0 || !targetColumn) return [];
    const yearMap = {};
    // Try to find a date/year column
    const cols = Object.keys(data[0]);
    const dateCol = cols.find(c => ['date','orderdate','year','month','timestamp','time'].some(kw => c.toLowerCase().includes(kw)));
    data.forEach(row => {
      let year = 'All';
      if (dateCol && row[dateCol]) {
        const parsed = new Date(row[dateCol]);
        if (!isNaN(parsed.getFullYear())) year = parsed.getFullYear().toString();
      }
      const val = parseFloat(row[targetColumn]);
      if (!isNaN(val)) {
        if (!yearMap[year]) yearMap[year] = { sum: 0, count: 0 };
        yearMap[year].sum += val;
        yearMap[year].count += 1;
      }
    });
    return Object.entries(yearMap)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([year, { sum, count }]) => ({ year, sales: Math.round(sum), avg: Math.round(sum / count), type: 'historical' }));
  };

  // Build forecast data with year labels from forecasting engine output
  const buildForecastBars = () => {
    if (!forecast || !forecast.forecast || forecast.forecast.length === 0) return [];
    return forecast.forecast.map(f => {
      const label = f.date ? f.date.substring(0, 7) : `Period ${f.period}`;
      return { year: label, sales: Math.round(f.value), lower: Math.round(f.lower_80), upper: Math.round(f.upper_80), type: 'forecast' };
    });
  };

  const historicalBars = buildYearlySalesTrend();
  const forecastBars = buildForecastBars();
  const combinedChartData = [
    ...historicalBars,
    ...forecastBars
  ];
  const hasDateData = historicalBars.length > 0;

  // Build class distribution from prediction result (for HR, healthcare, etc.)
  const classDistData = (prediction?.class_distribution || []).map((c, i) => ({
    ...c,
    fill: ['#6366f1','#10b981','#f59e0b','#ef4444','#8b5cf6','#06b6d4'][i % 6]
  }));

  const bestYear = historicalBars.length > 0 ? historicalBars.reduce((a, b) => a.sales > b.sales ? a : b) : null;
  const totalSales = historicalBars.reduce((s, r) => s + r.sales, 0);
  const avgYearlySales = historicalBars.length > 0 ? Math.round(totalSales / historicalBars.length) : 0;
  const latestHistorical = historicalBars[historicalBars.length - 1]?.sales || 0;
  const firstForecast = forecastBars[0]?.sales || 0;
  const isTrendUp = firstForecast > latestHistorical;
  const trendColor = isTrendUp ? '#10b981' : '#ef4444';
  const trendIcon = isTrendUp ? '↑' : '↓';

  // Domain-adaptive KPI labels
  const isClassification = prediction?.task_type === 'classification';
  const dominantClass = classDistData.length > 0 ? classDistData.reduce((a, b) => a.count > b.count ? a : b) : null;
  const minorityClass = classDistData.length > 1 ? classDistData.reduce((a, b) => a.count < b.count ? a : b) : null;

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const entry = payload[0]?.payload;
      const isForecast = entry?.type === 'forecast';
      const idx = combinedChartData.findIndex(d => d.year === label);
      const prev = idx > 0 ? combinedChartData[idx - 1]?.sales : null;
      const pctChange = prev ? (((entry.sales - prev) / prev) * 100).toFixed(1) : null;
      const isUp = pctChange > 0;
      return (
        <div style={{
          background: 'rgba(15,23,42,0.97)',
          border: `2px solid ${isForecast ? '#f59e0b' : '#6366f1'}`,
          borderRadius: '12px',
          padding: '14px 18px',
          minWidth: '200px',
          boxShadow: `0 8px 32px rgba(0,0,0,0.5)`
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
            <span style={{
              background: isForecast ? 'rgba(245,158,11,0.2)' : 'rgba(99,102,241,0.2)',
              color: isForecast ? '#f59e0b' : '#6366f1',
              fontSize: '11px', fontWeight: 700, padding: '3px 10px',
              borderRadius: '20px', textTransform: 'uppercase', letterSpacing: '0.5px'
            }}>
              {isForecast ? '🔮 AI Forecast' : '📊 Historical'}
            </span>
          </div>
          <p style={{ margin: '0 0 4px', color: '#94a3b8', fontSize: '12px' }}>Year / Period</p>
          <p style={{ margin: '0 0 10px', color: '#fff', fontSize: '18px', fontWeight: 800 }}>{label}</p>
          <p style={{ margin: '0 0 4px', color: '#94a3b8', fontSize: '12px' }}>{targetColumn}</p>
          <p style={{ margin: '0 0 8px', color: isForecast ? '#f59e0b' : '#818cf8', fontSize: '22px', fontWeight: 800 }}>
            {entry.sales?.toLocaleString()}
          </p>
          {pctChange !== null && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: '6px',
              color: isUp ? '#10b981' : '#ef4444',
              fontSize: '13px', fontWeight: 600,
              background: isUp ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
              padding: '4px 10px', borderRadius: '8px'
            }}>
              {isUp ? '↑' : '↓'} {Math.abs(pctChange)}% vs previous year
            </div>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="di-results-container">
      {/* Top Navigation / Header */}
      <div className="di-top-nav glass-card">
        <div className="di-nav-left">
          <h2 style={{ fontSize: '18px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
            {activeView === 'insights' ? <><TrendingUp size={20} color="var(--primary)" /> Future Insights</> : <><Lightbulb size={20} color="#f59e0b" /> Solutions & Actions</>}
          </h2>
          
          {prediction?.domain && (
            <div className="domain-badge" style={{ 
              marginLeft: '16px', 
              background: 'rgba(99,102,241,0.1)', 
              color: '#818cf8', 
              padding: '4px 12px', 
              borderRadius: '20px', 
              fontSize: '11px', 
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              border: '1px solid rgba(99,102,241,0.2)',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}>
              <Sparkles size={12} /> {prediction.domain}
            </div>
          )}
          
          <div className="target-selector-wrapper" style={{ marginLeft: '24px', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '12px', color: '#64748b', fontWeight: 600, textTransform: 'uppercase' }}>Predicting:</span>
            <select 
              value={currentTarget} 
              onChange={(e) => onTargetChange(e.target.value)}
              style={{
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.1)',
                color: '#fff',
                padding: '4px 12px',
                borderRadius: '6px',
                fontSize: '13px',
                outline: 'none',
                cursor: 'pointer'
              }}
            >
              {data && data.length > 0 && Object.keys(data[0]).map(col => (
                <option key={col} value={col}>{col}</option>
              ))}
            </select>
          </div>
        </div>
        <div className="di-nav-right">
          <div className="overall-score">
            <span>Overall AI Confidence:</span>
            <strong style={{ color: getConfidenceColor(overall_confidence?.level) }}>
              {overall_confidence?.level?.toUpperCase()} ({Math.round((overall_confidence?.score || 0) * 100)}%)
            </strong>
          </div>
          <button 
            onClick={() => setIsChatOpen(true)}
            className="di-chat-toggle-btn"
          >
            <MessageSquare size={16} /> Chat with AI
          </button>
        </div>
      </div>

      <AnimatePresence mode="wait">
        {activeView === 'insights' && (
          <motion.div key="insights" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="di-tab-content">

            {/* ── KPI Cards ── */}
            <div className="kpi-cards-row">
              <div className="kpi-card">
                <div className="kpi-icon" style={{ background: 'rgba(99,102,241,0.15)' }}><TrendingUp size={20} color="#6366f1" /></div>
                <div>
                  <div className="kpi-label">
                    {isClassification ? `Total ${currentTarget} Records` : `Avg Yearly ${currentTarget}`}
                  </div>
                  <div className="kpi-value" style={{ color: '#6366f1' }}>
                    {isClassification
                      ? (classDistData.reduce((s, c) => s + c.count, 0)).toLocaleString()
                      : avgYearlySales.toLocaleString()}
                  </div>
                </div>
              </div>
              <div className="kpi-card">
                <div className="kpi-icon" style={{ background: 'rgba(16,185,129,0.15)' }}><Target size={20} color="#10b981" /></div>
                <div>
                  <div className="kpi-label">
                    {isClassification ? `Majority Class` : `Best Historical Year`}
                  </div>
                  <div className="kpi-value" style={{ color: '#10b981' }}>
                    {isClassification
                      ? (dominantClass ? `${dominantClass.label} (${dominantClass.count.toLocaleString()})` : '—')
                      : (bestYear ? `${bestYear.year} (${bestYear.sales.toLocaleString()})` : '—')}
                  </div>
                </div>
              </div>
              <div className="kpi-card">
                <div className="kpi-icon" style={{ background: `rgba(${isTrendUp ? '16,185,129' : '239,68,68'},0.15)` }}>
                  <Activity size={20} color={isClassification ? '#f59e0b' : trendColor} />
                </div>
                <div>
                  <div className="kpi-label">{isClassification ? `Minority / At-Risk Class` : `Forecast Trend`}</div>
                  <div className="kpi-value" style={{ color: isClassification ? '#f59e0b' : trendColor }}>
                    {isClassification
                      ? (minorityClass ? `${minorityClass.label} (${minorityClass.count.toLocaleString()})` : '—')
                      : `${trendIcon} ${forecast?.trend_direction || (forecastBars.length > 0 ? (isTrendUp ? 'Upward' : 'Downward') : 'No Forecast')}`}
                  </div>
                </div>
              </div>
              <div className="kpi-card">
                <div className="kpi-icon" style={{ background: 'rgba(245,158,11,0.15)' }}><ShieldCheck size={20} color="#f59e0b" /></div>
                <div>
                  <div className="kpi-label">AI Confidence</div>
                  <div className="kpi-value" style={{ color: getConfidenceColor(prediction?.confidence?.level) }}>
                    {Math.round((prediction?.confidence?.score || 0) * 100)}% — {prediction?.confidence?.level?.toUpperCase()}
                  </div>
                </div>
              </div>
            </div>

            {/* ── Main Chart: Time-series OR Classification Distribution ── */}
            <div className="glass-card di-card" style={{ marginTop: '16px' }}>
              <div className="di-card-header">
                <div className="title-group">
                  <LineChartIcon size={20} color="#6366f1" />
                  <h3>
                    {hasDateData
                      ? `${currentTarget} Trend — Historical & Predicted Future`
                      : isClassification
                        ? `${currentTarget} Distribution — AI Prediction Breakdown`
                        : `${currentTarget} — Data Overview`}
                  </h3>
                </div>
                {hasDateData && (
                  <div style={{ display: 'flex', gap: '16px', fontSize: '13px', alignItems: 'center' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ width: 12, height: 12, borderRadius: 3, background: '#6366f1', display: 'inline-block' }}></span> Historical
                    </span>
                    {combinedChartData.some(d => d.type === 'forecast') && (
                      <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span style={{ width: 12, height: 12, borderRadius: 3, background: '#f59e0b', display: 'inline-block' }}></span> AI Forecast
                      </span>
                    )}
                  </div>
                )}
              </div>
              <div className="di-card-body">

                {/* ── TIME SERIES CHART (Sales, Finance, etc.) ── */}
                {hasDateData && (
                  <>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={combinedChartData} margin={{ top: 30, right: 20, left: 10, bottom: 20 }} barCategoryGap="30%">
                        <defs>
                          <linearGradient id="gradHistorical" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#818cf8" stopOpacity={1}/>
                            <stop offset="100%" stopColor="#4f46e5" stopOpacity={0.8}/>
                          </linearGradient>
                          <linearGradient id="gradForecast" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#fcd34d" stopOpacity={1}/>
                            <stop offset="100%" stopColor="#d97706" stopOpacity={0.8}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                        <XAxis dataKey="year" stroke="rgba(255,255,255,0.2)" tick={{ fontSize: 12, fill: '#94a3b8', fontWeight: 600 }} axisLine={{ stroke: 'rgba(255,255,255,0.1)' }} tickLine={false} />
                        <YAxis stroke="rgba(255,255,255,0.1)" tick={{ fontSize: 11, fill: '#64748b' }} tickFormatter={v => v >= 1000000 ? `${(v/1000000).toFixed(1)}M` : v >= 1000 ? `${(v/1000).toFixed(0)}K` : v} axisLine={false} tickLine={false} />
                        <RechartsTooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.04)', radius: 4 }} />
                        {combinedChartData.some(d => d.type === 'forecast') && historicalBars.length > 0 && (
                          <ReferenceLine x={historicalBars[historicalBars.length - 1].year} stroke="rgba(245,158,11,0.6)" strokeDasharray="6 3" strokeWidth={2}
                            label={{ value: '◀ History  |  AI Forecast ▶', position: 'top', fill: '#f59e0b', fontSize: 11, fontWeight: 700 }} />
                        )}
                        <Bar dataKey="sales" name={targetColumn} radius={[8, 8, 0, 0]} maxBarSize={70}>
                          {combinedChartData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.type === 'forecast' ? 'url(#gradForecast)' : 'url(#gradHistorical)'} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '24px', marginTop: '8px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div style={{ width: 14, height: 14, borderRadius: 4, background: 'linear-gradient(180deg, #818cf8, #4f46e5)' }}></div>
                        <span style={{ fontSize: '13px', color: '#94a3b8', fontWeight: 600 }}>Historical {targetColumn}</span>
                      </div>
                      {combinedChartData.some(d => d.type === 'forecast') && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <div style={{ width: 14, height: 14, borderRadius: 4, background: 'linear-gradient(180deg, #fcd34d, #d97706)' }}></div>
                          <span style={{ fontSize: '13px', color: '#94a3b8', fontWeight: 600 }}>AI Predicted {targetColumn}</span>
                        </div>
                      )}
                    </div>
                  </>
                )}

                {/* ── CLASSIFICATION DISTRIBUTION CHART (HR, Healthcare, etc.) ── */}
                {!hasDateData && isClassification && classDistData.length > 0 && (
                  <>
                    <div style={{ marginBottom: '16px', padding: '12px 16px', background: 'rgba(99,102,241,0.08)', borderRadius: '10px', borderLeft: '4px solid #6366f1' }}>
                      <p style={{ margin: 0, fontSize: '14px', color: 'var(--text)', lineHeight: 1.6 }}>
                        <strong style={{ color: '#818cf8' }}>How to read this chart:</strong> The bars show how many records fall into each {targetColumn} category in your dataset. The AI has learned the patterns behind each category and can now predict which category a new record will belong to.
                      </p>
                    </div>
                    <ResponsiveContainer width="100%" height={280}>
                      <BarChart data={classDistData} margin={{ top: 20, right: 20, left: 10, bottom: 20 }} barCategoryGap="35%">
                        <defs>
                          {classDistData.map((c, i) => (
                            <linearGradient key={i} id={`gradClass${i}`} x1="0" y1="0" x2="0" y2="1">
                              <stop offset="0%" stopColor={c.fill} stopOpacity={1}/>
                              <stop offset="100%" stopColor={c.fill} stopOpacity={0.6}/>
                            </linearGradient>
                          ))}
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                        <XAxis dataKey="label" stroke="rgba(255,255,255,0.2)" tick={{ fontSize: 13, fill: '#94a3b8', fontWeight: 700 }} axisLine={false} tickLine={false} />
                        <YAxis stroke="rgba(255,255,255,0.1)" tick={{ fontSize: 11, fill: '#64748b' }} tickFormatter={v => v.toLocaleString()} axisLine={false} tickLine={false} />
                        <RechartsTooltip
                          contentStyle={{ background: 'rgba(15,23,42,0.97)', border: '2px solid #6366f1', borderRadius: '12px', padding: '14px 18px' }}
                          formatter={(value, name) => [value.toLocaleString() + ' records', targetColumn]}
                          labelFormatter={label => `Category: ${label}`}
                        />
                        <Bar dataKey="count" radius={[10, 10, 0, 0]} maxBarSize={90}>
                          {classDistData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={`url(#gradClass${index})`} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '20px', marginTop: '10px', flexWrap: 'wrap' }}>
                      {classDistData.map((c, i) => {
                        const total = classDistData.reduce((s, x) => s + x.count, 0);
                        const pct = total > 0 ? ((c.count / total) * 100).toFixed(1) : 0;
                        return (
                          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <div style={{ width: 12, height: 12, borderRadius: 3, background: c.fill }}></div>
                            <span style={{ fontSize: '13px', color: '#94a3b8' }}>
                              <strong style={{ color: '#e2e8f0' }}>{c.label}</strong>: {c.count.toLocaleString()} ({pct}%)
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </>
                )}

                {/* ── FALLBACK: no date, not classification ── */}
                {!hasDateData && !isClassification && (
                  <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)' }}>
                    <TrendingUp size={40} color="#6366f1" style={{ marginBottom: '16px', opacity: 0.5 }} />
                    <p style={{ fontSize: '15px', margin: 0 }}>Add a date column to your dataset to see year-by-year trend analysis.</p>
                  </div>
                )}

                {/* AI business summary */}
                {prediction?.business_summary && !prediction.business_summary.startsWith('API Error') && (
                  <div style={{ background: 'rgba(99,102,241,0.07)', padding: '16px 20px', borderRadius: '8px', borderLeft: '4px solid #6366f1', marginTop: '16px' }}>
                    <p style={{ margin: 0, fontSize: '14px', lineHeight: '1.7', color: 'var(--text)' }}>
                      <strong style={{ color: '#6366f1' }}>🤖 AI Insight: </strong>{prediction.business_summary}
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* ── Bottom row: AI Confidence + Risk Detection ── */}
            <div className="di-grid-2" style={{ marginTop: '16px' }}>
              {/* Prediction confidence card */}
              {prediction && (
                <div className="glass-card di-card">
                  <div className="di-card-header">
                    <div className="title-group">
                      <Target size={20} color="var(--primary)" />
                      <h3>AI Prediction Confidence</h3>
                    </div>
                  </div>
                  <div className="di-card-body">
                    <ConfidenceBadge confidence={prediction.confidence} />
                    {prediction.predictions && prediction.predictions.length > 0 && (
                      <div className="prediction-chart mt-4">
                        <h4 style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '8px' }}>Actual vs Predicted Comparison (sample)</h4>
                        <ResponsiveContainer width="100%" height={160}>
                          <BarChart data={prediction.predictions.slice(0, 12)} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                            <XAxis dataKey="index" stroke="var(--text-muted)" tick={{ fontSize: 10 }} />
                            <YAxis stroke="var(--text-muted)" tick={{ fontSize: 10 }} />
                            <RechartsTooltip contentStyle={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', fontSize: '12px' }} />
                            <Bar dataKey="actual" name="Actual" fill="#8b5cf6" radius={[3,3,0,0]} />
                            <Bar dataKey="predicted" name="Predicted" fill="#10b981" radius={[3,3,0,0]} />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    )}
                    <button className="di-download-btn" style={{ marginTop: '8px' }}>
                      <Download size={14} /> Download Full Predictions
                    </button>
                  </div>
                </div>
              )}

              {/* Risk Detection */}
              {risk && (
                <div className="glass-card di-card">
                  <div className="di-card-header">
                    <div className="title-group">
                      <AlertTriangle size={20} color="#f59e0b" />
                      <h3>Risk & Anomaly Detection</h3>
                    </div>
                    <div className="risk-score-badge">
                      Risk Score: <strong style={{ color: (risk.risk_score || 0) > 50 ? '#ef4444' : '#10b981'}}>{(risk.risk_score || 0).toFixed(1)}</strong>
                    </div>
                  </div>
                  <div className="di-card-body">
                    <ConfidenceBadge confidence={risk.confidence} />
                    <div className="anomaly-stats" style={{ marginTop: '8px' }}>
                      <div className="stat-row">
                        <span>Total Records Checked</span>
                        <strong>{risk.total_records || 0}</strong>
                      </div>
                      <div className="stat-row">
                        <span>Anomalies Detected</span>
                        <strong style={{ color: (risk.anomaly_count || 0) > 0 ? '#ef4444' : '#10b981'}}>{risk.anomaly_count || 0}</strong>
                      </div>
                      <div className="stat-row">
                        <span>Anomaly Rate</span>
                        <strong>{((risk.anomaly_rate || 0) * 100).toFixed(1)}%</strong>
                      </div>
                    </div>
                    <ul className="alert-list" style={{ marginTop: '12px' }}>
                      {(risk.alerts || []).map((alert, idx) => (
                        <li key={idx}><AlertTriangle size={14} color="#f59e0b" /> {alert}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>

            {/* ── Key Business Drivers (RCA Integration) ── */}
            {rca && (
              <div className="glass-card di-card" style={{ marginTop: '16px' }}>
                <div className="di-card-header">
                  <div className="title-group">
                    <Activity size={20} color="#8b5cf6" />
                    <h3>Key Prediction Drivers — What's influencing the result?</h3>
                  </div>
                </div>
                <div className="di-card-body">
                  <p style={{ fontSize: '14px', color: '#94a3b8', marginBottom: '16px' }}>{rca.explanation}</p>
                  <div className="top-features">
                    {(rca.top_features || []).slice(0, 5).map((feat, idx) => (
                      <div key={idx} className="feature-bar-row" style={{ marginBottom: '12px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px', fontSize: '13px' }}>
                          <span className="feature-name" style={{ fontWeight: 600, color: '#e2e8f0' }}>{feat.feature}</span>
                          <span className="feature-impact" style={{ color: '#8b5cf6', fontWeight: 700 }}>{Math.round(feat.importance * 100)}% Impact</span>
                        </div>
                        <div className="feature-bar-bg" style={{ height: '8px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', overflow: 'hidden' }}>
                          <motion.div 
                            className="feature-bar-fill" 
                            initial={{ width: 0 }}
                            animate={{ width: `${feat.importance * 100}%` }}
                            transition={{ duration: 1, delay: idx * 0.1 }}
                            style={{ height: '100%', background: 'linear-gradient(90deg, #8b5cf6, #d8b4fe)', borderRadius: '4px' }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        )}

        {activeView === 'solutions' && (
          <motion.div key="solutions" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="di-tab-content">
            
            {/* Strategic Decision */}
            {decision && (
              <div className="glass-card di-card strategy-card">
                <div className="di-card-header">
                  <div className="title-group">
                    <Target size={22} color="var(--primary)" />
                    <h3>Executive Strategic Decision</h3>
                  </div>
                </div>
                <div className="di-card-body">
                  <ConfidenceBadge confidence={decision.confidence} />
                  
                  <div className="strategy-grid">
                    <div className="strategy-block">
                      <h4>Current Situation</h4>
                      <p>{decision.situation}</p>
                    </div>
                    <div className="strategy-block">
                      <h4>Key Finding</h4>
                      <p>{decision.key_finding}</p>
                    </div>
                    <div className="strategy-block highlight">
                      <h4>Strategic Decision</h4>
                      <p>{decision.strategic_decision}</p>
                    </div>
                  </div>

                  <div className="action-plan">
                    <h4>Recommended Action Plan</h4>
                    <ul>
                      {(decision.action_plan || []).map((step, idx) => (
                        <li key={idx}>
                          <div className="step-num">{idx + 1}</div>
                          <p>{step}</p>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}

            <div className="di-grid-2 mt-4">
              {/* RCA */}
              {rca && (
                <div className="glass-card di-card">
                  <div className="di-card-header">
                    <div className="title-group">
                      <Activity size={20} color="#8b5cf6" />
                      <h3>Root Cause Analysis (RCA)</h3>
                    </div>
                  </div>
                  <div className="di-card-body">
                    <ConfidenceBadge confidence={rca.confidence} />
                    <p className="rca-explanation">{rca.explanation}</p>
                    
                    <div className="causal-chain">
                      <h4>Causal Chain</h4>
                      <div className="chain-flow">
                        {(rca.causal_chain || []).map((link, idx) => (
                          <React.Fragment key={idx}>
                            <div className="chain-node">{link}</div>
                            {idx < (rca.causal_chain || []).length - 1 && <ArrowRight size={14} color="var(--text-muted)" />}
                          </React.Fragment>
                        ))}
                      </div>
                    </div>

                    <div className="top-features mt-4">
                      <h4>Key Business Drivers</h4>
                      {(rca.top_features || []).map((feat, idx) => (
                        <div key={idx} className="feature-bar-row">
                          <span className="feature-name">{feat.feature}</span>
                          <div className="feature-bar-bg">
                            <div 
                              className="feature-bar-fill" 
                              style={{ width: `${Math.min(100, Math.abs(feat.shap_value) * 100)}%`, background: feat.shap_value > 0 ? '#ef4444' : '#10b981' }} 
                            />
                          </div>
                          <span className="feature-val" title="Impact Score">{Math.abs(feat.shap_value).toFixed(2)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Recommendations */}
              {recommendation && (
                <div className="glass-card di-card">
                  <div className="di-card-header">
                    <div className="title-group">
                      <CheckCircle size={20} color="#10b981" />
                      <h3>Actionable Recommendations</h3>
                    </div>
                  </div>
                  <div className="di-card-body">
                    <ConfidenceBadge confidence={recommendation.confidence} />
                    <div className="recs-list">
                      {(recommendation.recommendations || []).map((rec, idx) => (
                        <div key={idx} className="rec-item">
                          <div className="rec-icon"><Lightbulb size={16} color="#f59e0b" /></div>
                          <div className="rec-content">
                            <h4>{rec.action || rec.strategy || `Strategy ${idx+1}`}</h4>
                            <p>{rec.description || rec.rationale || JSON.stringify(rec)}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>

          </motion.div>
        )}
      </AnimatePresence>

      {/* Chat Assistant Overlay */}
      <AnimatePresence>
        {isChatOpen && (
          <motion.div 
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className="di-chat-assistant glass-card"
          >
            <div className="di-chat-header">
              <div className="chat-title">
                <Brain size={18} color="var(--primary)" />
                <h4>Future Intelligence Assistant</h4>
              </div>
              <button onClick={() => setIsChatOpen(false)} className="close-btn"><X size={18} /></button>
            </div>
            
            <div className="di-chat-body" ref={chatBodyRef}>
              {chatMessages.map((msg, i) => (
                <div key={i} className={`chat-bubble ${msg.role}`}>
                  <div className="chat-avatar">
                    {msg.role === 'ai' ? <Brain size={14} color="white" /> : 'U'}
                  </div>
                  <div className="chat-text" style={{ whiteSpace: "pre-line" }}>{msg.text}</div>
                </div>
              ))}
              {isTyping && (
                <div className="chat-bubble ai">
                  <div className="chat-avatar">
                    <Brain size={14} color="white" />
                  </div>
                  <div className="chat-text typing-indicator">
                    <span></span><span></span><span></span>
                  </div>
                </div>
              )}
            </div>

            <form onSubmit={handleChatSubmit} className="di-chat-input-area">
              <input 
                type="text" 
                value={chatInput}
                onChange={e => setChatInput(e.target.value)}
                placeholder="Ask about the predictions or insights..."
                className="chat-input"
              />
              <button type="submit" className="chat-send-btn" disabled={!chatInput.trim()}>
                <Send size={16} />
              </button>
            </form>
          </motion.div>
        )}
      </AnimatePresence>

      <style>{`
        .di-setup-state {
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 40px;
          height: 100%;
        }
        .auto-run-card {
          max-width: 600px;
          width: 100%;
          padding: 40px;
          display: flex;
          flex-direction: column;
          align-items: center;
          text-align: center;
        }
        .icon-wrapper {
          width: 64px;
          height: 64px;
          background: rgba(99, 102, 241, 0.1);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          margin: 0 auto 20px;
        }
        .di-header h2 {
          font-size: 24px;
          font-weight: 700;
          margin-bottom: 12px;
        }
        .di-header p {
          color: var(--text-dim);
          font-size: 15px;
          line-height: 1.6;
          max-width: 450px;
          margin: 0 auto 30px;
        }
        .di-auto-config {
          width: 100%;
          display: flex;
          flex-direction: column;
          gap: 12px;
          margin-bottom: 30px;
          text-align: left;
        }
        .config-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.08);
          padding: 16px 20px;
          border-radius: var(--radius-md);
        }
        .config-label {
          font-size: 13px;
          color: var(--text-muted);
          font-weight: 600;
          text-transform: uppercase;
        }
        .config-value {
          font-size: 14px;
          font-weight: 500;
          color: var(--text);
        }
        .config-value.highlight {
          color: var(--primary);
          background: rgba(99, 102, 241, 0.15);
          padding: 4px 10px;
          border-radius: var(--radius-full);
        }
        .di-error {
          width: 100%;
          padding: 12px;
          background: rgba(239, 68, 68, 0.1);
          color: #ef4444;
          border: 1px solid rgba(239, 68, 68, 0.2);
          border-radius: var(--radius-md);
          margin-bottom: 20px;
          font-size: 14px;
        }
        .di-run-btn {
          width: 100%;
          background: linear-gradient(135deg, var(--primary), var(--accent));
          color: white;
          border: none;
          padding: 16px;
          border-radius: var(--radius-md);
          font-weight: 600;
          font-size: 16px;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 10px;
          cursor: pointer;
          transition: transform 0.2s, box-shadow 0.2s;
          box-shadow: 0 4px 14px rgba(99, 102, 241, 0.3);
        }
        .di-run-btn:hover {
          transform: translateY(-2px);
          box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
        }

        /* KPI Cards Row */
        .kpi-cards-row {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 14px;
          margin-bottom: 4px;
        }
        .kpi-card {
          background: rgba(255,255,255,0.04);
          border: 1px solid rgba(255,255,255,0.08);
          border-radius: 12px;
          padding: 16px 18px;
          display: flex;
          align-items: center;
          gap: 14px;
          transition: background 0.2s;
        }
        .kpi-card:hover {
          background: rgba(255,255,255,0.07);
        }
        .kpi-icon {
          width: 42px;
          height: 42px;
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }
        .kpi-label {
          font-size: 11px;
          color: var(--text-muted);
          text-transform: uppercase;
          font-weight: 600;
          letter-spacing: 0.5px;
          margin-bottom: 4px;
        }
        .kpi-value {
          font-size: 17px;
          font-weight: 700;
        }
        @media (max-width: 900px) {
          .kpi-cards-row { grid-template-columns: repeat(2, 1fr); }
        }

        .di-loading-state {
          display: flex;
          align-items: center;
          justify-content: center;
          height: 100%;
        }
        .di-loader-card {
          padding: 50px;
          text-align: center;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 16px;
          max-width: 500px;
        }
        .pulse-ring {
          width: 90px;
          height: 90px;
          border-radius: 50%;
          background: rgba(99, 102, 241, 0.1);
          display: flex;
          align-items: center;
          justify-content: center;
          margin-bottom: 10px;
          animation: pulse-ring 2s infinite;
        }
        @keyframes pulse-ring {
          0% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.4); }
          70% { box-shadow: 0 0 0 20px rgba(99, 102, 241, 0); }
          100% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0); }
        }
        .di-progress-bar {
          width: 100%;
          height: 6px;
          background: rgba(255,255,255,0.05);
          border-radius: 10px;
          margin-top: 20px;
          overflow: hidden;
        }
        .di-progress-fill {
          height: 100%;
          background: var(--primary);
        }

        .di-results-container {
          display: flex;
          flex-direction: column;
          gap: 20px;
          height: 100%;
        }
        .di-top-nav {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 20px;
        }
        .di-nav-left {
          display: flex;
          gap: 10px;
        }
        .di-tab-btn {
          background: transparent;
          border: 1px solid transparent;
          color: var(--text-dim);
          padding: 8px 16px;
          border-radius: var(--radius-md);
          display: flex;
          align-items: center;
          gap: 8px;
          cursor: pointer;
          font-weight: 500;
          transition: all 0.2s;
        }
        .di-tab-btn:hover {
          background: rgba(255,255,255,0.05);
        }
        .di-tab-btn.active {
          background: rgba(99, 102, 241, 0.1);
          border-color: rgba(99, 102, 241, 0.3);
          color: var(--primary);
        }
        .overall-score {
          font-size: 14px;
          display: flex;
          gap: 8px;
          align-items: center;
        }

        .di-tab-content {
          flex: 1;
          overflow-y: auto;
          display: flex;
          flex-direction: column;
          padding-bottom: 40px;
        }
        .di-grid-2 {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 20px;
        }
        .di-grid-2.single-column {
          grid-template-columns: 1fr;
        }

        .di-card {
          display: flex;
          flex-direction: column;
        }
        .di-card-header {
          padding: 16px 20px;
          border-bottom: 1px solid var(--glass-border);
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .title-group {
          display: flex;
          align-items: center;
          gap: 10px;
        }
        .title-group h3 {
          font-size: 16px;
          font-weight: 600;
        }
        .di-card-body {
          padding: 20px;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .confidence-badge {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px;
          border-radius: var(--radius-md);
          border: 1px solid;
        }
        .confidence-score {
          font-size: 20px;
          font-weight: 800;
        }
        .confidence-info {
          display: flex;
          flex-direction: column;
        }
        .confidence-level {
          font-size: 13px;
          font-weight: 700;
          text-transform: uppercase;
        }
        .confidence-desc {
          font-size: 12px;
          color: var(--text-dim);
        }

        .metric-row {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 12px;
        }
        .metric-box {
          background: rgba(0,0,0,0.2);
          padding: 12px;
          border-radius: var(--radius-sm);
          display: flex;
          flex-direction: column;
          align-items: center;
          text-align: center;
        }
        .metric-label {
          font-size: 11px;
          color: var(--text-muted);
          text-transform: uppercase;
        }
        .metric-value {
          font-size: 16px;
          font-weight: 600;
          margin-top: 4px;
          color: var(--primary);
        }

        .prediction-chart h4 {
          font-size: 13px;
          color: var(--text-muted);
          margin-bottom: 12px;
        }
        
        .di-download-btn {
          width: 100%;
          padding: 10px;
          background: rgba(99, 102, 241, 0.1);
          border: 1px solid rgba(99, 102, 241, 0.2);
          color: var(--primary);
          border-radius: var(--radius-md);
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          cursor: pointer;
          font-weight: 500;
          transition: background 0.2s;
        }
        .di-download-btn:hover {
          background: rgba(99, 102, 241, 0.2);
        }

        .alert-list {
          list-style: none;
          padding: 0;
          margin: 16px 0 0;
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .alert-list li {
          display: flex;
          align-items: flex-start;
          gap: 8px;
          font-size: 13px;
          color: var(--text-dim);
          background: rgba(245, 158, 11, 0.05);
          padding: 8px 12px;
          border-radius: var(--radius-sm);
          border: 1px solid rgba(245, 158, 11, 0.1);
        }

        .anomaly-stats {
          display: flex;
          flex-direction: column;
          gap: 12px;
          justify-content: center;
        }
        .stat-row {
          display: flex;
          justify-content: space-between;
          padding-bottom: 8px;
          border-bottom: 1px dashed var(--glass-border);
          font-size: 14px;
        }

        .strategy-grid {
          display: grid;
          grid-template-columns: 1fr 1fr 1fr;
          gap: 16px;
        }
        .strategy-block {
          background: rgba(0,0,0,0.2);
          padding: 16px;
          border-radius: var(--radius-md);
        }
        .strategy-block h4 {
          font-size: 12px;
          color: var(--text-muted);
          text-transform: uppercase;
          margin-bottom: 8px;
        }
        .strategy-block p {
          font-size: 14px;
          line-height: 1.5;
        }
        .strategy-block.highlight {
          background: rgba(99, 102, 241, 0.1);
          border: 1px solid rgba(99, 102, 241, 0.3);
        }
        .strategy-block.highlight h4 {
          color: var(--primary);
        }
        .strategy-block.highlight p {
          color: white;
          font-weight: 500;
        }

        .action-plan {
          margin-top: 20px;
        }
        .action-plan h4 {
          font-size: 15px;
          margin-bottom: 16px;
        }
        .action-plan ul {
          list-style: none;
          padding: 0;
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .action-plan li {
          display: flex;
          gap: 16px;
          align-items: center;
          background: rgba(255,255,255,0.02);
          padding: 12px 16px;
          border-radius: var(--radius-md);
          border: 1px solid var(--glass-border);
        }
        .step-num {
          background: var(--primary);
          color: white;
          width: 24px;
          height: 24px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 700;
          font-size: 12px;
          flex-shrink: 0;
        }

        .rca-explanation {
          font-size: 14px;
          line-height: 1.6;
          color: var(--text-dim);
        }
        .chain-flow {
          display: flex;
          align-items: center;
          gap: 8px;
          flex-wrap: wrap;
          margin-top: 12px;
        }
        .chain-node {
          background: rgba(139, 92, 246, 0.1);
          color: #c4b5fd;
          border: 1px solid rgba(139, 92, 246, 0.3);
          padding: 6px 12px;
          border-radius: var(--radius-full);
          font-size: 12px;
        }

        .feature-bar-row {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 8px;
        }
        .feature-name {
          width: 100px;
          font-size: 12px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        .feature-bar-bg {
          flex: 1;
          height: 8px;
          background: rgba(255,255,255,0.05);
          border-radius: 4px;
          overflow: hidden;
        }
        .feature-bar-fill {
          height: 100%;
          border-radius: 4px;
        }
        .feature-val {
          width: 40px;
          text-align: right;
          font-size: 12px;
          font-family: var(--font-mono);
        }

        .recs-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .rec-item {
          display: flex;
          gap: 12px;
          padding: 16px;
          background: rgba(0,0,0,0.2);
          border-radius: var(--radius-md);
          border-left: 3px solid #10b981;
        }
        .rec-content h4 {
          font-size: 14px;
          margin-bottom: 4px;
        }
        .rec-content p {
          font-size: 13px;
          color: var(--text-dim);
          line-height: 1.5;
        }

        /* Chat Assistant Styles */
        .di-chat-toggle-btn {
          background: rgba(99, 102, 241, 0.15);
          border: 1px solid rgba(99, 102, 241, 0.3);
          color: var(--primary);
          padding: 8px 16px;
          border-radius: var(--radius-full);
          display: flex;
          align-items: center;
          gap: 8px;
          font-weight: 600;
          font-size: 13px;
          cursor: pointer;
          transition: all 0.2s;
        }
        .di-chat-toggle-btn:hover {
          background: rgba(99, 102, 241, 0.25);
          transform: translateY(-1px);
        }

        .di-chat-assistant {
          position: fixed;
          bottom: 24px;
          right: 24px;
          width: 380px;
          height: 500px;
          border-radius: var(--radius-lg);
          display: flex;
          flex-direction: column;
          box-shadow: 0 10px 40px rgba(0,0,0,0.4);
          border: 1px solid rgba(255,255,255,0.1);
          background: rgba(15, 23, 42, 0.85);
          backdrop-filter: blur(20px);
          z-index: 100;
          overflow: hidden;
        }
        
        .di-chat-header {
          padding: 16px;
          background: rgba(0,0,0,0.3);
          border-bottom: 1px solid rgba(255,255,255,0.05);
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .chat-title {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .chat-title h4 {
          margin: 0;
          font-size: 14px;
          font-weight: 600;
        }
        .close-btn {
          background: transparent;
          border: none;
          color: var(--text-muted);
          cursor: pointer;
          padding: 4px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: var(--radius-sm);
        }
        .close-btn:hover {
          background: rgba(255,255,255,0.1);
          color: white;
        }

        .di-chat-body {
          flex: 1;
          padding: 16px;
          overflow-y: auto;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .chat-bubble {
          display: flex;
          gap: 12px;
          max-width: 90%;
        }
        .chat-bubble.ai {
          align-self: flex-start;
        }
        .chat-bubble.user {
          align-self: flex-end;
          flex-direction: row-reverse;
        }
        
        .chat-avatar {
          width: 28px;
          height: 28px;
          border-radius: 50%;
          background: var(--primary);
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          font-size: 12px;
          font-weight: bold;
        }
        .chat-bubble.user .chat-avatar {
          background: rgba(255,255,255,0.1);
        }

        .chat-text {
          background: rgba(0,0,0,0.3);
          padding: 12px 14px;
          border-radius: 12px;
          font-size: 13px;
          line-height: 1.5;
          color: var(--text);
        }
        .chat-bubble.ai .chat-text {
          border-top-left-radius: 2px;
          background: rgba(99, 102, 241, 0.1);
          border: 1px solid rgba(99, 102, 241, 0.2);
        }
        .chat-bubble.user .chat-text {
          border-top-right-radius: 2px;
          background: rgba(255,255,255,0.05);
        }

        .di-chat-input-area {
          padding: 16px;
          border-top: 1px solid rgba(255,255,255,0.05);
          display: flex;
          gap: 8px;
          background: rgba(0,0,0,0.2);
        }
        .chat-input {
          flex: 1;
          background: rgba(0,0,0,0.3);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: var(--radius-full);
          padding: 10px 16px;
          color: white;
          font-size: 13px;
          outline: none;
        }
        .chat-input:focus {
          border-color: var(--primary);
        }
        .chat-send-btn {
          width: 38px;
          height: 38px;
          border-radius: 50%;
          background: var(--primary);
          color: white;
          border: none;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: background 0.2s;
        }
        .chat-send-btn:disabled {
          background: rgba(255,255,255,0.1);
          color: var(--text-muted);
          cursor: not-allowed;
        }
        .chat-send-btn:not(:disabled):hover {
          background: var(--accent);
        }
        
        .typing-indicator {
          display: flex;
          gap: 4px;
          align-items: center;
          padding: 14px 18px !important;
        }
        .typing-indicator span {
          width: 6px;
          height: 6px;
          background-color: var(--text-dim);
          border-radius: 50%;
          animation: typing 1.4s infinite ease-in-out both;
        }
        .typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
        .typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
        @keyframes typing {
          0%, 80%, 100% { transform: scale(0); }
          40% { transform: scale(1); }
        }

      `}</style>
    </div>
  );
};

export default DecisionIntelligenceView;
