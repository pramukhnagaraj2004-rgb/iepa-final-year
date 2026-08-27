import React, { useState } from 'react';
import axios from 'axios';
import ExercisePanel from './ExercisePanel';
import ConceptResult from './ConceptResult';
import { useAuth } from '../context/AuthContext';

export default function FeedbackPanel({
    feedbackData,
    executionData,
    exerciseState,
    onCheckCode,
    onSubmitAnswers,
    submitResult,
    onContinueNext,
    onRetry,
}) {
    const { API_BASE } = useAuth();
    const [explanation, setExplanation] = useState(null);
    const [loadingExplanation, setLoadingExplanation] = useState(false);

    const handleReveal = async () => {
        setLoadingExplanation(true);
        try {
            const res = await axios.post(`${API_BASE}/curriculum/reveal-explanation/${feedbackData.concept}`);
            setExplanation(res.data.data.explanation);
        } catch (e) {
            setExplanation("Couldn't load explanation right now.");
        }
        setLoadingExplanation(false);
    };

    if (submitResult) {
        return <ConceptResult result={submitResult} onContinueNext={onContinueNext} onRetry={onRetry} />;
    }

    return (
        <div className="bg-[#12121A] rounded-2xl border border-[#2A2A3E] flex flex-col overflow-hidden">
            <div className="px-5 py-3.5 bg-[#1A1A2E] border-b border-[#2A2A3E] font-bold text-[#94A3B8] text-xs tracking-wider uppercase">
                Feedback & Learning
            </div>

            <div className="p-6 flex-1 overflow-y-auto space-y-6">
                {!feedbackData && !executionData && (
                    <div className="flex-1 flex flex-col items-center justify-center text-[#94A3B8] gap-3 py-16 text-center">
                        <p className="italic text-sm">Run some code to get feedback here.</p>
                    </div>
                )}

                {executionData && !feedbackData && (
                    <div className="p-4 rounded-xl bg-[#10B981]/10 border border-[#10B981]/30 text-[#10B981] font-semibold text-sm">
                        ✅ Code ran successfully with no errors!
                    </div>
                )}

                {feedbackData && (
                    <div className="space-y-4">
                        <div className="text-[10px] font-bold uppercase tracking-wide text-[#94A3B8]">
                            {feedbackData.tier} feedback
                        </div>
                        <div className="text-base leading-relaxed text-[#F1F5F9] whitespace-pre-wrap">
                            {feedbackData.feedback}
                        </div>

                        {feedbackData.tier === 'hint' && !explanation && (
                            <button
                                onClick={handleReveal}
                                disabled={loadingExplanation}
                                className="text-xs font-semibold text-[#6C63FF] underline"
                            >
                                {loadingExplanation ? 'Loading...' : 'View Full Explanation'}
                            </button>
                        )}
                        {explanation && (
                            <div className="bg-[#1A1A2E] border border-[#2A2A3E] rounded-xl p-4 text-sm text-[#F1F5F9]">
                                {explanation}
                            </div>
                        )}
                        {feedbackData.tier === 'exercise' && feedbackData.follow_up_exercise && (
                            <div className="bg-[#F59E0B]/10 border border-[#F59E0B]/30 rounded-xl p-4 text-sm text-[#F1F5F9]">
                                {feedbackData.follow_up_exercise}
                            </div>
                        )}
                    </div>
                )}

                {exerciseState && (
                    <ExercisePanel
                        concept={feedbackData?.concept}
                        exerciseState={exerciseState}
                        onCheckCode={onCheckCode}
                        onSubmitAnswers={onSubmitAnswers}
                    />
                )}
            </div>
        </div>
    );
}