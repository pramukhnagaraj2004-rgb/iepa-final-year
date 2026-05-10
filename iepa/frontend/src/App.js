import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Editor from '@monaco-editor/react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const API_BASE = 'http://127.0.0.1:8000';

function App() {
  const [learnerId, setLearnerId] = useState('student_001');
  const [health, setHealth] = useState(false);
  
  const [code, setCode] = useState("def add(a, b):\n    return a + b\n\nadd(1, '2')");
  const [errorRaw, setErrorRaw] = useState("TypeError: unsupported operand type(s) for +: 'int' and 'str'");
  
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState(null);
  
  const [feedbackData, setFeedbackData] = useState(null);
  const [masteryData, setMasteryData] = useState([]);
  const [historyData, setHistoryData] = useState([]);

  useEffect(() => {
    checkHealth();
  }, []);

  useEffect(() => {
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
        const mastery = res.data.data.mastery;
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
    try {
      const res = await axios.post(`${API_BASE}/analyze`, {
        learner_id: learnerId,
        code: code,
        error_raw: errorRaw
      });
      if (res.data.success) {
        setFeedbackData(res.data.data);
        fetchMastery();
        fetchHistory();
      } else {
        setApiError(res.data.error || 'Unknown API error');
      }
    } catch (e) {
      setApiError(e.message || 'Failed to connect to API');
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
    if (score > 0.4) return '#22c55e'; // green
    if (score >= 0.2) return '#eab308'; // yellow
    return '#ef4444'; // red
  };

  return (
    <div className="min-h-screen bg-gray-50 font-sans text-gray-900 pb-12">
      {/* HEADER */}
      <header className="bg-indigo-600 text-white p-4 shadow-md flex justify-between items-center">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold tracking-tight hidden md:block">IEPA — Intelligent Error Pattern Analyzer</h1>
          <h1 className="text-xl font-bold tracking-tight md:hidden">IEPA</h1>
          <div className={`w-3 h-3 rounded-full ${health ? 'bg-green-400' : 'bg-red-400'} shadow-sm border border-white/20`} title={health ? "API Online" : "API Offline"}></div>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium opacity-90 hidden sm:block">Learner ID:</label>
          <input 
            type="text" 
            value={learnerId} 
            onChange={(e) => setLearnerId(e.target.value)}
            className="px-3 py-1.5 text-gray-900 font-mono text-sm rounded border-none focus:ring-2 focus:ring-indigo-300 outline-none w-32 sm:w-auto"
          />
        </div>
      </header>

      {/* ERROR BANNER */}
      {apiError && (
        <div className="bg-red-500 text-white p-3 text-center shadow-inner font-medium">
          ⚠️ {apiError}
        </div>
      )}

      <main className="p-4 md:p-6 max-w-7xl mx-auto space-y-6 md:space-y-8 mt-2">
        
        {/* TOP ROW: Editor + Feedback */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* CODE EDITOR PANEL */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden flex flex-col">
            <div className="p-3 bg-gray-50 border-b border-gray-200 font-bold text-gray-700 text-sm tracking-wide uppercase">
              1. Your Code & Error
            </div>
            <div className="h-[400px] border-b border-gray-200">
              <Editor
                height="100%"
                defaultLanguage="python"
                theme="vs-dark"
                value={code}
                onChange={setCode}
                options={{ minimap: { enabled: false }, fontSize: 14, padding: { top: 16 } }}
              />
            </div>
            <div className="p-5 flex flex-col gap-3">
              <label className="font-semibold text-sm text-gray-700">Terminal Error Output:</label>
              <textarea 
                value={errorRaw}
                onChange={(e) => setErrorRaw(e.target.value)}
                className="w-full h-24 p-3 rounded-lg border border-gray-300 font-mono text-sm bg-gray-50 focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none resize-y transition-colors"
                placeholder="Paste your python error here..."
              />
              <button 
                onClick={handleAnalyze}
                disabled={loading || !errorRaw.trim()}
                className="mt-2 w-full py-3.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-lg shadow-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center gap-2"
              >
                {loading ? (
                  <span className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></span>
                ) : 'Analyze Error'}
              </button>
            </div>
          </div>

          {/* FEEDBACK PANEL */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 flex flex-col">
            <div className="p-3 bg-gray-50 border-b border-gray-200 font-bold text-gray-700 text-sm tracking-wide uppercase">
              2. Pedagogical Feedback
            </div>
            <div className="p-6 flex-1 flex flex-col">
              {!feedbackData ? (
                <div className="flex-1 flex flex-col items-center justify-center text-gray-400 gap-3">
                  <svg className="w-12 h-12 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                  <p className="italic">Submit an error to see AI-generated feedback</p>
                </div>
              ) : (
                <div className="space-y-6 animate-fade-in">
                  {/* Metadata Row */}
                  <div className="flex flex-wrap gap-4 items-center">
                    <div className="px-3 py-1 rounded-full bg-blue-100 text-blue-800 text-sm font-bold border border-blue-200 shadow-sm">
                      {feedbackData.concept.replace(/_/g, ' ')}
                    </div>
                    
                    <div className={`px-3 py-1 rounded-full text-sm font-bold border uppercase tracking-wider shadow-sm ${getTierColor(feedbackData.tier)}`}>
                      Tier: {feedbackData.tier}
                    </div>

                    <div className="flex items-center gap-2 text-sm text-gray-600 ml-auto bg-gray-100 px-3 py-1 rounded-full">
                      <span className="font-medium">Confidence:</span>
                      <div className="w-20 h-2 bg-gray-300 rounded-full overflow-hidden">
                        <div className="h-full bg-blue-500 rounded-full" style={{width: `${feedbackData.confidence * 100}%`}}></div>
                      </div>
                      <span className="font-mono font-bold">{(feedbackData.confidence * 100).toFixed(0)}%</span>
                    </div>
                  </div>

                  {/* Feedback Content */}
                  <div className="bg-gray-50 rounded-xl p-5 border border-gray-200 text-lg leading-relaxed text-gray-800 whitespace-pre-wrap shadow-inner">
                    {feedbackData.feedback}
                  </div>

                  {/* Follow-up Exercise */}
                  {feedbackData.tier === 'exercise' && feedbackData.follow_up_exercise && (
                    <div className="bg-orange-50 border border-orange-200 rounded-xl p-5 shadow-sm">
                      <h3 className="font-bold text-orange-800 mb-3 flex items-center gap-2">
                        <span className="text-xl">📝</span> Follow-up Exercise
                      </h3>
                      <p className="text-orange-900 whitespace-pre-wrap font-medium">{feedbackData.follow_up_exercise}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* MASTERY DASHBOARD */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-bold text-gray-800 mb-6 uppercase tracking-wide">Concept Mastery Dashboard</h2>
          {masteryData.length === 0 ? (
            <div className="text-gray-400 italic text-center py-10">No mastery data available yet. Start practicing!</div>
          ) : (
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={masteryData} margin={{ top: 5, right: 20, bottom: 40, left: 0 }}>
                  <XAxis 
                    dataKey="concept" 
                    angle={-45} 
                    textAnchor="end" 
                    height={80} 
                    tick={{fontSize: 12, fill: '#4b5563'}} 
                    interval={0}
                    tickFormatter={(val) => val.replace(/_/g, ' ')}
                  />
                  <YAxis domain={[0, 1]} tick={{fontSize: 12, fill: '#4b5563'}} tickFormatter={(val) => `${val * 100}%`} />
                  <Tooltip 
                    cursor={{fill: '#f3f4f6'}} 
                    contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'}} 
                    formatter={(value) => [`${(value * 100).toFixed(1)}%`, 'Mastery']}
                    labelFormatter={(label) => label.replace(/_/g, ' ')}
                  />
                  <Bar dataKey="score" radius={[4, 4, 0, 0]} maxBarSize={60}>
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
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="p-6 border-b border-gray-200 bg-gray-50">
            <h2 className="text-lg font-bold text-gray-800 uppercase tracking-wide">Recent Error History</h2>
          </div>
          {historyData.length === 0 ? (
            <div className="text-gray-400 italic text-center py-8">No history found for this learner.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-white text-gray-500 text-xs uppercase tracking-wider">
                    <th className="p-4 font-semibold border-b border-gray-200">Attempt</th>
                    <th className="p-4 font-semibold border-b border-gray-200">Concept</th>
                    <th className="p-4 font-semibold border-b border-gray-200">Confidence</th>
                    <th className="p-4 font-semibold border-b border-gray-200">Feedback Tier</th>
                    <th className="p-4 font-semibold border-b border-gray-200">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="text-sm">
                  {historyData.map((item, idx) => (
                    <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                      <td className="p-4 text-gray-500 font-mono">#{historyData.length - idx}</td>
                      <td className="p-4 font-semibold text-gray-800">{item.concept.replace(/_/g, ' ')}</td>
                      <td className="p-4 font-mono text-gray-600">{(item.confidence * 100).toFixed(1)}%</td>
                      <td className="p-4">
                        <span className={`px-2 py-1 rounded text-xs uppercase font-bold shadow-sm ${getTierColor(item.tier)}`}>
                          {item.tier}
                        </span>
                      </td>
                      <td className="p-4 text-gray-500">{new Date(item.timestamp).toLocaleString()}</td>
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

export default App;
