import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import Editor from '@monaco-editor/react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

import { AuthProvider, useAuth } from './context/AuthContext';
import Landing from './pages/Landing';
import AuthCallback from './pages/AuthCallback';

function Dashboard() {
  const { user, logout, API_BASE, fetchMe } = useAuth();
  
  const [health, setHealth] = useState(false);
  const [code, setCode] = useState("def calculate_average(nums):\n    total = 0\n    for i in range(len(nums) + 1):\n        total += nums[i]\n    return total / len(nums)\n\ncalculate_average([10, 20, 30])");
  
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState(null);
  const [quotaWarning, setQuotaWarning] = useState(null);
  
  const [feedbackData, setFeedbackData] = useState(null);
  const [executionData, setExecutionData] = useState(null);
  const [masteryData, setMasteryData] = useState([]);
  const [historyData, setHistoryData] = useState([]);

  const learnerId = user?.google_id || user?.sub || user?.email || 'default_student';

  useEffect(() => {
    checkHealth();
    if (learnerId) {
      fetchMastery();
      fetchHistory();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [learnerId]);

  const checkHealth = async () => {
    try {
      const res = await axios.get(`${API_BASE}/health`);
      setHealth(res.data.success);
    } catch (e) {
      setHealth(false);
    }
  };

  const fetchMastery = async () => {
    try {
      const res = await axios.get(`${API_BASE}/learner/${learnerId}/mastery`);
      if (res.data.success) {
        const mastery = res.data.data.mastery || {};
        const formatted = Object.keys(mastery).map(key => ({
          concept: key,
          score: mastery[key]
        }));
        setMasteryData(formatted);
      }
    } catch (e) {
      if (e.response && e.response.status !== 404) console.error(e);
      setMasteryData([]);
    }
  };

  const fetchHistory = async () => {
    try {
      const res = await axios.get(`${API_BASE}/learner/${learnerId}/history`);
      if (res.data.success) {
        const reversed = [...res.data.data].reverse();
        setHistoryData(reversed.slice(0, 10));
      }
    } catch (e) {
      if (e.response && e.response.status !== 404) console.error(e);
      setHistoryData([]);
    }
  };

  const handleAnalyze = async () => {
    setLoading(true);
    setApiError(null);
    setQuotaWarning(null);
    setFeedbackData(null);
    setExecutionData(null);

    try {
      const res = await axios.post(`${API_BASE}/analyze`, {
        learner_id: learnerId,
        code: code,
        language: "python"
      });

      if (res.data.success) {
        const payload = res.data.data;
        if (payload.concept) {
          // An error occurred and feedback was generated
          setFeedbackData(payload);
          setExecutionData(payload.execution || null);
        } else {
          // Clean run with no errors
          setExecutionData(payload.execution || { stdout: payload.stdout, success: true, error_raw: "" });
        }
        
        fetchMastery();
        fetchHistory();
        if (user) {
          const token = localStorage.getItem('iepa_token');
          if (token) fetchMe(token);
        }
      } else {
        setApiError(res.data.error || 'Unknown API error');
      }
    } catch (e) {
      if (e.response && e.response.status === 429) {
        setQuotaWarning(e.response.data.error || 'Monthly analysis limit reached.');
      } else {
        setApiError(e.response?.data?.error || e.message || 'Failed to connect to API');
      }
    } finally {
      setLoading(false);
    }
  };

  const getTierColor = (tier) => {
    switch(tier) {
      case 'hint': return 'bg-green-100 text-green-800 border-green-300';
      case 'explain': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'exercise': return 'bg-red-100 text-red-800 border-red-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getBarColor = (score) => {
    if (score > 0.4) return '#22c55e';
    if (score >= 0.2) return '#eab308';
    return '#ef4444';
  };

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900 pb-12">
      {/* HEADER */}
      <header className="bg-indigo-600 text-white px-6 py-3.5 shadow-md flex justify-between items-center sticky top-0 z-30">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-white/20 flex items-center justify-center font-bold text-sm">
            IE
          </div>
          <h1 className="text-xl font-bold tracking-tight hidden sm:block">IEPA Dashboard</h1>
          <div className={`w-2.5 h-2.5 rounded-full ${health ? 'bg-green-400' : 'bg-red-400'} shadow-sm`} title={health ? "API Online" : "API Offline"}></div>
        </div>

        {/* User Quota & Profile */}
        <div className="flex items-center gap-4">
          {user && (
            <div className="flex items-center gap-3 bg-indigo-700/50 px-3 py-1.5 rounded-xl border border-indigo-500/30">
              {user.picture ? (
                <img src={user.picture} alt="Avatar" className="w-7 h-7 rounded-full border border-white/30" />
              ) : (
                <div className="w-7 h-7 rounded-full bg-indigo-500 flex items-center justify-center text-xs font-bold uppercase">
                  {user.name ? user.name[0] : 'U'}
                </div>
              )}
              <div className="text-xs hidden md:block text-left">
                <div className="font-semibold">{user.name || 'Student'}</div>
                <div className="text-indigo-200">
                  {user.tier === 'pro' ? 'Pro Tier (Unlimited)' : `${user.analyses_remaining ?? (20 - (user.analyses_this_month || 0))} analyses left`}
                </div>
              </div>
            </div>
          )}

          <button
            onClick={logout}
            className="px-3.5 py-1.5 bg-white/10 hover:bg-white/20 transition-colors font-medium rounded-lg text-xs"
          >
            Sign Out
          </button>
        </div>
      </header>

      {/* ERROR BANNER */}
      {apiError && (
        <div className="bg-red-600 text-white px-4 py-3 text-center font-medium shadow-sm flex items-center justify-center gap-2">
          <span>⚠️</span> {apiError}
        </div>
      )}

      {/* QUOTA WARNING BANNER */}
      {quotaWarning && (
        <div className="bg-amber-500 text-slate-950 px-4 py-3 text-center font-semibold shadow-sm flex items-center justify-center gap-2">
          <span>🔒</span> {quotaWarning}
        </div>
      )}

      <main className="p-4 md:p-6 max-w-7xl mx-auto space-y-6 mt-2">
        
        {/* TOP ROW: Code Sandbox & Execution Panel */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* CODE EDITOR PANEL */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden flex flex-col">
            <div className="px-5 py-3.5 bg-slate-50 border-b border-slate-200 font-bold text-slate-700 text-xs tracking-wider uppercase flex justify-between items-center">
              <span>1. Python Code Sandbox (Docker Isolated)</span>
              <span className="text-indigo-600 lowercase font-mono">python 3.11</span>
            </div>
            
            <div className="h-[380px] border-b border-slate-200">
              <Editor
                height="100%"
                defaultLanguage="python"
                theme="vs-dark"
                value={code}
                onChange={setCode}
                options={{ minimap: { enabled: false }, fontSize: 13, padding: { top: 12 } }}
              />
            </div>

            <div className="p-4 bg-slate-50/50 flex items-center justify-between gap-3">
              <span className="text-xs text-slate-500">Submits code directly into isolated sandbox environment</span>
              <button 
                onClick={handleAnalyze}
                disabled={loading || !code.trim()}
                className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl shadow-md hover:shadow-indigo-500/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 text-sm"
              >
                {loading ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                    Executing in Docker...
                  </>
                ) : (
                  <>
                    <span>▶ Run & Analyze Code</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* PEDAGOGICAL FEEDBACK PANEL */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 flex flex-col overflow-hidden">
            <div className="px-5 py-3.5 bg-slate-50 border-b border-slate-200 font-bold text-slate-700 text-xs tracking-wider uppercase">
              2. Pedagogical Feedback & Diagnostic
            </div>

            <div className="p-6 flex-1 flex flex-col">
              {!feedbackData && !executionData ? (
                <div className="flex-1 flex flex-col items-center justify-center text-slate-400 gap-3 py-16">
                  <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center text-xl">💡</div>
                  <p className="italic text-sm">Click "Run & Analyze Code" to execute in the Docker sandbox</p>
                </div>
              ) : executionData && !feedbackData ? (
                <div className="space-y-4">
                  <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 font-semibold flex items-center gap-2 text-sm">
                    <span>✅</span> Code executed successfully with zero runtime errors!
                  </div>
                  {executionData.stdout && (
                    <div className="bg-slate-900 text-slate-100 p-4 rounded-xl font-mono text-xs overflow-x-auto whitespace-pre-wrap">
                      <div className="text-slate-400 mb-1 text-[11px] uppercase tracking-wider">Standard Output:</div>
                      {executionData.stdout}
                    </div>
                  )}
                </div>
              ) : (
                <div className="space-y-5 animate-fade-in">
                  {/* Metadata Row */}
                  <div className="flex flex-wrap gap-3 items-center">
                    <div className="px-3 py-1 rounded-full bg-indigo-100 text-indigo-800 text-xs font-bold border border-indigo-200 uppercase tracking-wide">
                      {feedbackData.concept.replace(/_/g, ' ')}
                    </div>
                    
                    <div className={`px-3 py-1 rounded-full text-xs font-bold border uppercase tracking-wider ${getTierColor(feedbackData.tier)}`}>
                      Tier: {feedbackData.tier}
                    </div>

                    <div className="flex items-center gap-2 text-xs text-slate-600 ml-auto bg-slate-100 px-3 py-1 rounded-full">
                      <span className="font-medium">Confidence:</span>
                      <span className="font-mono font-bold">{(feedbackData.confidence * 100).toFixed(0)}%</span>
                    </div>
                  </div>

                  {/* Captured Error Trace */}
                  {feedbackData.error_raw && (
                    <div className="p-3 bg-red-50/80 border border-red-200 rounded-xl font-mono text-xs text-red-900 overflow-x-auto">
                      <span className="font-bold text-red-700 mr-2">Captured:</span> {feedbackData.error_raw}
                    </div>
                  )}

                  {/* Feedback Content */}
                  <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 text-base leading-relaxed text-slate-800 whitespace-pre-wrap shadow-inner">
                    {feedbackData.feedback}
                  </div>

                  {/* Follow-up Exercise */}
                  {feedbackData.tier === 'exercise' && feedbackData.follow_up_exercise && (
                    <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 space-y-1 shadow-sm">
                      <div className="font-bold text-amber-900 text-xs uppercase tracking-wide flex items-center gap-1.5">
                        <span>📝</span> Practice Exercise
                      </div>
                      <p className="text-amber-950 text-sm font-medium whitespace-pre-wrap">{feedbackData.follow_up_exercise}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* MASTERY DASHBOARD */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xs font-bold text-slate-700 uppercase tracking-wider">Concept Mastery Overview</h2>
            <span className="text-xs text-slate-500">Live Bayesian Tracking</span>
          </div>

          {masteryData.length === 0 ? (
            <div className="text-slate-400 italic text-center py-8 text-sm">No mastery records yet. Submit code to begin tracking!</div>
          ) : (
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={masteryData} margin={{ top: 5, right: 20, bottom: 40, left: 0 }}>
                  <XAxis 
                    dataKey="concept" 
                    angle={-30} 
                    textAnchor="end" 
                    height={60} 
                    tick={{fontSize: 11, fill: '#64748b'}} 
                    interval={0}
                    tickFormatter={(val) => val.replace(/_/g, ' ')}
                  />
                  <YAxis domain={[0, 1]} tick={{fontSize: 11, fill: '#64748b'}} tickFormatter={(val) => `${val * 100}%`} />
                  <Tooltip 
                    cursor={{fill: '#f1f5f9'}} 
                    contentStyle={{borderRadius: '10px', border: '1px solid #e2e8f0'}} 
                    formatter={(value) => [`${(value * 100).toFixed(0)}%`, 'Mastery']}
                    labelFormatter={(label) => label.replace(/_/g, ' ')}
                  />
                  <Bar dataKey="score" radius={[6, 6, 0, 0]} maxBarSize={45}>
                    {masteryData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={getBarColor(entry.score)} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* HISTORY PANEL */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-200 bg-slate-50">
            <h2 className="text-xs font-bold text-slate-700 uppercase tracking-wider">Recent Diagnostic History</h2>
          </div>
          {historyData.length === 0 ? (
            <div className="text-slate-400 italic text-center py-6 text-sm">No history records logged yet.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-white text-slate-500 text-xs uppercase tracking-wider border-b border-slate-200">
                    <th className="p-3.5 font-semibold">Attempt</th>
                    <th className="p-3.5 font-semibold">Concept</th>
                    <th className="p-3.5 font-semibold">Confidence</th>
                    <th className="p-3.5 font-semibold">Feedback Tier</th>
                    <th className="p-3.5 font-semibold">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="text-xs">
                  {historyData.map((item, idx) => (
                    <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50 transition-colors">
                      <td className="p-3.5 text-slate-500 font-mono">#{historyData.length - idx}</td>
                      <td className="p-3.5 font-semibold text-slate-800">{item.concept.replace(/_/g, ' ')}</td>
                      <td className="p-3.5 font-mono text-slate-600">{(item.confidence * 100).toFixed(0)}%</td>
                      <td className="p-3.5">
                        <span className={`px-2.5 py-0.5 rounded text-[10px] uppercase font-bold border ${getTierColor(item.tier)}`}>
                          {item.tier}
                        </span>
                      </td>
                      <td className="p-3.5 text-slate-500">{new Date(item.timestamp).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

      </main>
    </div>
  );
}

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) {
    return <div className="min-h-screen flex items-center justify-center bg-slate-50 text-indigo-600 font-bold">Loading...</div>;
  }
  if (!user) {
    return <Navigate to="/" replace />;
  }
  return children;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/auth/callback" element={<AuthCallback />} />
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } 
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
