import React from 'react';
import Editor from '@monaco-editor/react';

export default function CodeSandbox({
    code, setCode, onAnalyze, loading, feedbackData, executionData,
    gateActive, gateConceptLabel, verifyingGate, gateResult,
    onVerifyGate, onTryDifferent, onExitGate,
}) {
    const stdout = gateActive ? gateResult?.stdout : executionData?.stdout;

    return (
        <div className="bg-[#12121A] rounded-2xl border border-[#2A2A3E] overflow-hidden flex flex-col">
            <div className="px-5 py-3.5 bg-[#1A1A2E] border-b border-[#2A2A3E] font-bold text-[#94A3B8] text-xs tracking-wider uppercase flex justify-between items-center">
                <span>Python Code Sandbox • Docker Isolated</span>
            </div>

            {gateActive && (
                <div className="px-5 py-3 bg-[#6C63FF]/10 border-b border-[#6C63FF]/30 flex items-center justify-between gap-3">
                    <span className="text-xs text-[#F1F5F9]">
                        🔒 Practicing <strong>{gateConceptLabel}</strong> — fix this bug, then Verify to unlock the exercises.
                    </span>
                    <button onClick={onExitGate} className="text-xs text-[#94A3B8] underline shrink-0">
                        Exit practice
                    </button>
                </div>
            )}

            <div className="h-[340px] border-b border-[#2A2A3E]">
                <Editor
                    height="100%"
                    defaultLanguage="python"
                    theme="vs-dark"
                    value={code}
                    onChange={setCode}
                    options={{ minimap: { enabled: false }, fontSize: 13, padding: { top: 12 } }}
                />
            </div>

            {stdout && (
                <div className="border-b border-[#2A2A3E]">
                    <div className="px-4 pt-2.5 pb-1 text-[10px] font-bold uppercase tracking-wider text-[#94A3B8]">
                        Console Output
                    </div>
                    <pre className="px-4 pb-3 text-xs font-mono text-[#10B981] whitespace-pre-wrap max-h-[100px] overflow-y-auto">
                        {stdout}
                    </pre>
                </div>
            )}

            <div className="p-4 flex flex-col gap-3">
                {gateActive ? (
                    <>
                        <div className="flex items-center gap-3">
                            <button
                                onClick={onVerifyGate}
                                disabled={verifyingGate || !code.trim()}
                                className="px-6 py-3 bg-[#6C63FF] hover:bg-[#5A52E8] text-white font-bold rounded-xl shadow-md transition-all disabled:opacity-50 text-sm"
                            >
                                {verifyingGate ? 'Checking...' : '✓ Verify Fix'}
                            </button>
                            <button
                                onClick={onTryDifferent}
                                className="px-4 py-3 bg-[#1A1A2E] border border-[#2A2A3E] hover:border-[#6C63FF] text-[#F1F5F9] text-sm font-semibold rounded-xl"
                            >
                                🔀 Try a different example
                            </button>
                        </div>
                        {gateResult && (
                            <div className={`p-3 rounded-lg text-xs font-mono ${gateResult.correct ? 'bg-[#10B981]/10 border border-[#10B981]/30 text-[#10B981]' :
                                'bg-[#EF4444]/10 border border-[#EF4444]/30 text-[#EF4444]'}`}>
                                {gateResult.correct ? '✓ Fixed! Loading exercises...' : (gateResult.error_raw || 'Still has an error — try again.')}
                            </div>
                        )}
                    </>
                ) : (
                    <>
                        <div className="flex items-center justify-between gap-3">
                            <span className="text-xs text-[#94A3B8]">Submits to isolated sandbox</span>
                            <button
                                onClick={onAnalyze}
                                disabled={loading || !code.trim()}
                                className="px-6 py-3 bg-[#6C63FF] hover:bg-[#5A52E8] text-white font-bold rounded-xl shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                            >
                                {loading ? 'Running...' : '▶ Run & Analyze Code'}
                            </button>
                        </div>

                        {feedbackData?.concept && (
                            <div className="space-y-2 pt-2 border-t border-[#2A2A3E]">
                                <div className="flex flex-wrap gap-2">
                                    <span className="px-2.5 py-1 rounded-full bg-[#6C63FF]/15 text-[#6C63FF] text-xs font-bold uppercase">
                                        {feedbackData.concept.replace(/_/g, ' ')}
                                    </span>
                                    <span className={`px-2.5 py-1 rounded-full text-xs font-bold uppercase
                    ${feedbackData.tier === 'hint' ? 'bg-[#10B981]/15 text-[#10B981]' :
                                            feedbackData.tier === 'explain' ? 'bg-[#F59E0B]/15 text-[#F59E0B]' :
                                                'bg-[#EF4444]/15 text-[#EF4444]'}`}>
                                        {feedbackData.tier}
                                    </span>
                                </div>
                                {feedbackData.error_raw && (
                                    <div className="p-3 bg-[#EF4444]/10 border border-[#EF4444]/30 rounded-lg font-mono text-xs text-[#EF4444] overflow-x-auto">
                                        {feedbackData.error_raw}
                                    </div>
                                )}
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}