import React, { useState, useEffect } from 'react';
import Editor from '@monaco-editor/react';

export default function ExercisePanel({ concept, exerciseState, onCheckCode, onSubmitAnswers }) {
    const { theory, coding } = exerciseState;
    const [theoryAnswer, setTheoryAnswer] = useState(null);
    const [codeAnswers, setCodeAnswers] = useState(coding.map((q) => q.buggy_code || ''));
    const [codeResults, setCodeResults] = useState(coding.map(() => null)); // null | true | false
    const [checking, setChecking] = useState(coding.map(() => false));

    useEffect(() => {
        setTheoryAnswer(null);
        setCodeAnswers(coding.map((q) => q.buggy_code || ''));
        setCodeResults(coding.map(() => null));
        setChecking(coding.map(() => false));
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [concept, theory?.id]);

    const handleCheck = async (idx) => {
        const next = [...checking];
        next[idx] = true;
        setChecking(next);

        const res = await onCheckCode(coding[idx].id, codeAnswers[idx]);

        const nextResults = [...codeResults];
        nextResults[idx] = res.correct;
        setCodeResults(nextResults);

        const nextChecking = [...checking];
        nextChecking[idx] = false;
        setChecking(nextChecking);
    };

    const canSubmit = theoryAnswer !== null && codeResults.every((r) => r !== null);

    return (
        <div className="pt-4 border-t border-[#2A2A3E] space-y-6">
            <div className="text-sm font-bold text-[#F1F5F9]">
                Test Your Understanding — {concept?.replace(/_/g, ' ')}
            </div>

            {/* Theory question */}
            <div className="space-y-2">
                <p className="text-sm text-[#F1F5F9]">{theory.question}</p>
                <div className="space-y-1.5">
                    {theory.options.map((opt) => {
                        const letter = opt.trim()[0];
                        return (
                            <label
                                key={letter}
                                className={`flex items-center gap-2 px-3 py-2 rounded-lg border cursor-pointer text-sm
                  ${theoryAnswer === letter ? 'border-[#6C63FF] bg-[#6C63FF]/10' : 'border-[#2A2A3E] hover:bg-[#1A1A2E]'}`}
                            >
                                <input
                                    type="radio"
                                    name={`theory-${theory.id}`}
                                    checked={theoryAnswer === letter}
                                    onChange={() => setTheoryAnswer(letter)}
                                    className="accent-[#6C63FF]"
                                />
                                <span className="text-[#F1F5F9]">{opt}</span>
                            </label>
                        );
                    })}
                </div>
            </div>

            {/* Coding questions */}
            {coding.map((q, idx) => (
                <div key={q.id} className="space-y-2">
                    <div className="text-sm font-semibold text-[#F1F5F9]">
                        Coding Challenge {idx + 1}
                    </div>
                    <p className="text-sm text-[#94A3B8]">{q.description}</p>
                    <div className="h-[150px] rounded-lg overflow-hidden border border-[#2A2A3E]">
                        <Editor
                            height="100%"
                            defaultLanguage="python"
                            theme="vs-dark"
                            value={codeAnswers[idx]}
                            onChange={(val) => {
                                const next = [...codeAnswers];
                                next[idx] = val;
                                setCodeAnswers(next);
                            }}
                            options={{ minimap: { enabled: false }, fontSize: 12 }}
                        />
                    </div>
                    <div className="flex items-center gap-3">
                        <button
                            onClick={() => handleCheck(idx)}
                            disabled={checking[idx]}
                            className="px-4 py-1.5 bg-[#1A1A2E] border border-[#2A2A3E] hover:border-[#6C63FF] text-[#F1F5F9] text-xs font-semibold rounded-lg"
                        >
                            {checking[idx] ? 'Checking...' : 'Run & Check'}
                        </button>
                        {codeResults[idx] === true && <span className="text-[#10B981] text-xs font-bold">✓ Correct</span>}
                        {codeResults[idx] === false && <span className="text-[#EF4444] text-xs font-bold">✗ Not quite — try again</span>}
                    </div>
                </div>
            ))}

            <button
                onClick={() => onSubmitAnswers(theoryAnswer, codeResults)}
                disabled={!canSubmit}
                className="w-full py-3 bg-[#6C63FF] hover:bg-[#5A52E8] disabled:opacity-40 disabled:cursor-not-allowed text-white font-bold rounded-xl text-sm"
            >
                Submit All Answers
            </button>
        </div>
    );
}