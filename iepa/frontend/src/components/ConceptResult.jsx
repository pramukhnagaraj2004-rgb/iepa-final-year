import React from 'react';

export default function ConceptResult({ result, onContinueNext, onRetry }) {
    const { passed, score, wrong_answers, resources, next_concept } = result;

    return (
        <div className="p-6 space-y-5">
            <div className={`p-4 rounded-xl font-bold text-sm
        ${passed ? 'bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/30' :
                    'bg-[#EF4444]/15 text-[#EF4444] border border-[#EF4444]/30'}`}>
                {passed ? `Concept Passed! 🎉 Score: ${score}/3` : `Score: ${score}/3 — Retest available`}
            </div>

            {wrong_answers?.length > 0 && (
                <div className="space-y-3">
                    {wrong_answers.map((w) => (
                        <div key={w.question_id} className="bg-[#1A1A2E] border border-[#2A2A3E] rounded-xl p-4 text-sm space-y-1">
                            <div className="text-[#F1F5F9] font-semibold">{w.question}</div>
                            <div className="text-[#94A3B8]">Your answer: <span className="text-[#EF4444]">{w.your_answer}</span></div>
                            <div className="text-[#94A3B8]">Correct answer: <span className="text-[#10B981]">{w.correct_answer}</span></div>
                            <div className="text-[#F1F5F9] pt-1">{w.explanation}</div>
                        </div>
                    ))}
                </div>
            )}

            {passed && resources?.length > 0 && (
                <div className="space-y-2">
                    <div className="text-xs font-bold uppercase text-[#94A3B8]">Deep Dive Resources</div>
                    {resources.map((r) => (
                        <a
                            key={r.url}
                            href={r.url}
                            target="_blank"
                            rel="noreferrer"
                            className="block bg-[#1A1A2E] border border-[#2A2A3E] hover:border-[#6C63FF] rounded-lg p-3 text-sm"
                        >
                            <div className="text-[#6C63FF] font-semibold">{r.title}</div>
                            <div className="text-[#94A3B8] text-xs">{r.description}</div>
                        </a>
                    ))}
                </div>
            )}

            {passed && next_concept && (
                <button
                    onClick={onContinueNext}
                    className="w-full py-3 bg-[#6C63FF] hover:bg-[#5A52E8] text-white font-bold rounded-xl text-sm"
                >
                    Continue to: {next_concept.replace(/_/g, ' ')}
                </button>
            )}

            {!passed && (
                <button
                    onClick={onRetry}
                    className="w-full py-3 bg-[#1A1A2E] border border-[#2A2A3E] hover:border-[#6C63FF] text-[#F1F5F9] font-bold rounded-xl text-sm"
                >
                    Try Again
                </button>
            )}
        </div>
    );
}