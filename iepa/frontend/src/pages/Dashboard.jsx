import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

import { useAuth } from '../context/AuthContext';
import Sidebar from '../components/Sidebar';
import CodeSandbox from '../components/CodeSandbox';
import FeedbackPanel from '../components/FeedbackPanel';

export default function Dashboard() {
    const { user, logout, API_BASE, fetchMe } = useAuth();
    const learnerId = user?.google_id || user?.sub || user?.email || 'default_student';

    const [code, setCode] = useState(
        "def calculate_average(nums):\n    total = 0\n    for i in range(len(nums) + 1):\n        total += nums[i]\n    return total / len(nums)\n\ncalculate_average([10, 20, 30])"
    );
    const [loading, setLoading] = useState(false);
    const [apiError, setApiError] = useState(null);
    const [quotaWarning, setQuotaWarning] = useState(null);
    const [feedbackData, setFeedbackData] = useState(null);
    const [executionData, setExecutionData] = useState(null);
    const [historyData, setHistoryData] = useState([]);

    const [concepts, setConcepts] = useState([]);
    const [progress, setProgress] = useState({});
    const [activeConcept, setActiveConcept] = useState(null);
    const [exerciseState, setExerciseState] = useState(null);
    const [submitResult, setSubmitResult] = useState(null);

    // --- Gate (concept practice) state ---
    const [gateActive, setGateActive] = useState(false);
    const [gateConcept, setGateConcept] = useState(null);
    const [gatePool, setGatePool] = useState([]);
    const [gateQuestionId, setGateQuestionId] = useState(null);
    const [verifyingGate, setVerifyingGate] = useState(false);
    const [gateResult, setGateResult] = useState(null);

    const fetchHistory = useCallback(async () => {
        try {
            const res = await axios.get(`${API_BASE}/learner/${learnerId}/history`);
            if (res.data.success) {
                setHistoryData([...res.data.data].reverse().slice(0, 10));
            }
        } catch (e) {
            setHistoryData([]);
        }
    }, [API_BASE, learnerId]);

    const fetchCurriculum = useCallback(async () => {
        try {
            const [conceptsRes, progressRes] = await Promise.all([
                axios.get(`${API_BASE}/curriculum/concepts`),
                axios.get(`${API_BASE}/curriculum/progress`),
            ]);
            if (conceptsRes.data.success) setConcepts(conceptsRes.data.data);
            if (progressRes.data.success) {
                setProgress(progressRes.data.data.concepts);
                if (!activeConcept) setActiveConcept(progressRes.data.data.current_concept);
            }
        } catch (e) {
            console.error('Failed to load curriculum', e);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [API_BASE]);

    useEffect(() => {
        fetchHistory();
        fetchCurriculum();
    }, [fetchHistory, fetchCurriculum]);

    const loadExercise = async (concept) => {
        setSubmitResult(null);
        try {
            const res = await axios.get(`${API_BASE}/curriculum/exercise/${concept}`);
            if (res.data.success) setExerciseState(res.data.data);
        } catch (e) {
            setExerciseState(null);
        }
    };

    const loadReview = async (concept) => {
        setExerciseState(null);
        try {
            const res = await axios.get(`${API_BASE}/curriculum/review/${concept}`);
            if (res.data.success) setSubmitResult(res.data.data);
        } catch (e) {
            setSubmitResult(null);
        }
    };

    const pickRandom = (pool, excludeId) => {
        const options = pool.filter((q) => q.id !== excludeId);
        const list = options.length > 0 ? options : pool;
        return list[Math.floor(Math.random() * list.length)];
    };

    const enterPracticeMode = async (concept) => {
        setActiveConcept(concept);
        setFeedbackData(null);
        setExecutionData(null);
        setExerciseState(null);
        setSubmitResult(null);
        setGateResult(null);
        setGateActive(true);
        setGateConcept(concept);

        try {
            const res = await axios.get(`${API_BASE}/curriculum/gate/${concept}`);
            if (res.data.success) {
                const pool = res.data.data.pool;
                setGatePool(pool);
                const chosen = pickRandom(pool, null);
                setGateQuestionId(chosen.id);
                setCode(chosen.buggy_code);
            }
        } catch (e) {
            setGateActive(false);
            setGateConcept(null);
            setApiError('Could not load practice exercise for this concept.');
        }
    };

    const handleTryDifferent = () => {
        if (gatePool.length === 0) return;
        const chosen = pickRandom(gatePool, gateQuestionId);
        setGateQuestionId(chosen.id);
        setCode(chosen.buggy_code);
        setGateResult(null);
    };

    const handleVerifyGate = async () => {
        setVerifyingGate(true);
        setGateResult(null);
        try {
            const res = await axios.post(
                `${API_BASE}/curriculum/check-code/${gateConcept}/${gateQuestionId}`,
                { code }
            );
            const result = res.data.data;
            setGateResult(result);
            if (result.correct) {
                setGateActive(false);
                await loadExercise(gateConcept);
            }
        } catch (e) {
            setGateResult({ correct: false, error_raw: e.message });
        } finally {
            setVerifyingGate(false);
        }
    };

    const handleExitGate = () => {
        setGateActive(false);
        setGateConcept(null);
        setGateResult(null);
        setExerciseState(null);
    };

    const handleSelectConcept = (concept) => {
        if (progress[concept]?.status === 'passed') {
            setActiveConcept(concept);
            setGateActive(false);
            setGateConcept(null);
            loadReview(concept);
        } else {
            enterPracticeMode(concept);
        }
    };

    const handleAnalyze = async () => {
        setLoading(true);
        setApiError(null);
        setQuotaWarning(null);
        setFeedbackData(null);
        setExecutionData(null);
        setSubmitResult(null);

        try {
            const res = await axios.post(`${API_BASE}/analyze`, { learner_id: learnerId, code, language: 'python' });
            if (res.data.success) {
                const payload = res.data.data;
                if (payload.concept) {
                    setFeedbackData(payload);
                    setExecutionData(payload.execution || null);
                } else {
                    setExecutionData(payload.execution || { stdout: payload.stdout, success: true, error_raw: '' });
                }
                fetchHistory();
                const token = localStorage.getItem('iepa_token');
                if (token) fetchMe(token);
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

    const handleCheckCode = async (questionId, submittedCode) => {
        try {
            const res = await axios.post(
                `${API_BASE}/curriculum/check-code/${activeConcept}/${questionId}`,
                { code: submittedCode }
            );
            return res.data.data;
        } catch (e) {
            return { correct: false, error_raw: e.message };
        }
    };

    const handleSubmitAnswers = async (theoryAnswer, codeResults) => {
        try {
            const res = await axios.post(`${API_BASE}/curriculum/submit/${activeConcept}`, {
                theory_answer: theoryAnswer,
                coding_results: codeResults,
            });
            if (res.data.success) {
                setSubmitResult(res.data.data);
                fetchCurriculum();
            }
        } catch (e) {
            setApiError(e.response?.data?.error || e.message);
        }
    };

    const handleContinueNext = (nextConcept) => {
        setSubmitResult(null);
        setExerciseState(null);
        if (nextConcept) {
            enterPracticeMode(nextConcept);
        }
    };

    const handleRetry = () => {
        setSubmitResult(null);
        loadExercise(activeConcept);
    };

    const gateConceptLabel = concepts.find((c) => c.name === gateConcept)?.display_name || gateConcept;

    return (
        <div className="min-h-screen bg-[#0A0A0F] text-[#F1F5F9] flex">
            <Sidebar
                concepts={concepts}
                progress={progress}
                activeConcept={activeConcept}
                onSelectConcept={handleSelectConcept}
                user={user}
                analysesRemaining={user?.analyses_remaining}
                tier={user?.tier}
            />

            <div className="flex-1 flex flex-col min-w-0">
                <header className="h-14 border-b border-[#2A2A3E] flex items-center justify-between px-6 shrink-0">
                    <span className="font-bold tracking-tight">IEPA</span>
                    <button
                        onClick={logout}
                        className="px-3 py-1.5 bg-[#1A1A2E] border border-[#2A2A3E] hover:border-[#6C63FF] rounded-lg text-xs font-semibold"
                    >
                        Sign Out
                    </button>
                </header>

                {apiError && (
                    <div className="bg-[#EF4444] text-white px-4 py-2.5 text-center text-sm font-medium">{apiError}</div>
                )}
                {quotaWarning && (
                    <div className="bg-[#F59E0B] text-black px-4 py-2.5 text-center text-sm font-semibold">{quotaWarning}</div>
                )}

                <main className="flex-1 overflow-y-auto p-6 space-y-6">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <CodeSandbox
                            code={code}
                            setCode={setCode}
                            onAnalyze={handleAnalyze}
                            loading={loading}
                            feedbackData={feedbackData}
                            executionData={executionData}
                            gateActive={gateActive}
                            gateConceptLabel={gateConceptLabel}
                            verifyingGate={verifyingGate}
                            gateResult={gateResult}
                            onVerifyGate={handleVerifyGate}
                            onTryDifferent={handleTryDifferent}
                            onExitGate={handleExitGate}
                        />
                        <FeedbackPanel
                            feedbackData={feedbackData}
                            executionData={executionData}
                            exerciseState={exerciseState}
                            onCheckCode={handleCheckCode}
                            onSubmitAnswers={handleSubmitAnswers}
                            submitResult={submitResult}
                            onContinueNext={() => handleContinueNext(submitResult?.next_concept)}
                            onRetry={handleRetry}
                            onPracticeConcept={enterPracticeMode}
                            progress={progress}
                        />
                    </div>

                    <div className="bg-[#12121A] rounded-2xl border border-[#2A2A3E] overflow-hidden">
                        <div className="px-6 py-4 border-b border-[#2A2A3E]">
                            <h2 className="text-xs font-bold text-[#94A3B8] uppercase tracking-wider">Recent Diagnostic History</h2>
                        </div>
                        {historyData.length === 0 ? (
                            <div className="text-[#94A3B8] italic text-center py-6 text-sm">No history yet.</div>
                        ) : (
                            <div className="overflow-x-auto">
                                <table className="w-full text-left border-collapse text-xs">
                                    <thead>
                                        <tr className="text-[#94A3B8] uppercase tracking-wider border-b border-[#2A2A3E]">
                                            <th className="p-3">Attempt</th>
                                            <th className="p-3">Concept</th>
                                            <th className="p-3">Error Captured</th>
                                            <th className="p-3">Tier</th>
                                            <th className="p-3">Time</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {historyData.map((item, idx) => (
                                            <tr key={idx} className="border-b border-[#2A2A3E]">
                                                <td className="p-3 font-mono text-[#94A3B8]">#{historyData.length - idx}</td>
                                                <td className="p-3 font-semibold">{item.concept.replace(/_/g, ' ')}</td>
                                                <td className="p-3 font-mono text-[#EF4444] max-w-xs truncate">{item.error_raw || '—'}</td>
                                                <td className="p-3 uppercase font-bold">{item.tier}</td>
                                                <td className="p-3 text-[#94A3B8]">{new Date(item.timestamp).toLocaleString()}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </main>
            </div>
        </div>
    );
}