import React from 'react';
import { Lock, CheckCircle2, Circle, CircleDot } from 'lucide-react';

const STATUS_STYLE = {
    locked: { icon: Lock, color: '#94A3B8', label: 'Locked' },
    unlocked: { icon: CircleDot, color: '#6C63FF', label: 'Unlocked' },
    attempted: { icon: Circle, color: '#F59E0B', label: 'Attempted' },
    passed: { icon: CheckCircle2, color: '#10B981', label: 'Passed' },
};

export default function Sidebar({
    concepts,        // ordered list from GET /curriculum/concepts
    progress,        // map from GET /curriculum/progress -> concepts
    activeConcept,
    onSelectConcept,
    user,
    analysesRemaining,
    tier,
}) {
    return (
        <aside className="w-[240px] shrink-0 bg-[#12121A] border-r border-[#2A2A3E] flex flex-col h-full">
            {/* User info */}
            <div className="p-4 border-b border-[#2A2A3E]">
                <div className="flex items-center gap-2.5">
                    {user?.picture ? (
                        <img src={user.picture} alt="avatar" className="w-9 h-9 rounded-full" />
                    ) : (
                        <div className="w-9 h-9 rounded-full bg-[#6C63FF] flex items-center justify-center text-sm font-bold">
                            {user?.name ? user.name[0] : 'U'}
                        </div>
                    )}
                    <div className="min-w-0">
                        <div className="text-sm font-semibold text-[#F1F5F9] truncate">{user?.name || 'Student'}</div>
                        <div className="text-[10px] uppercase tracking-wide font-bold text-[#6C63FF]">
                            {tier === 'pro' ? 'PRO' : 'FREE'}
                        </div>
                    </div>
                </div>
                {tier !== 'pro' && (
                    <div className="mt-2 text-xs text-[#94A3B8]">
                        {analysesRemaining ?? 20}/20 analyses left
                    </div>
                )}
            </div>

            {/* Curriculum list */}
            <div className="flex-1 overflow-y-auto p-3">
                <div className="text-[10px] font-bold uppercase tracking-wider text-[#94A3B8] px-1 mb-2">
                    Python Curriculum
                </div>
                <div className="space-y-1">
                    {concepts.map((c) => {
                        const state = progress?.[c.name];
                        const status = state?.status || 'locked';
                        const { icon: Icon, color } = STATUS_STYLE[status];
                        const isActive = activeConcept === c.name;
                        const isLocked = status === 'locked';

                        return (
                            <button
                                key={c.name}
                                disabled={isLocked}
                                onClick={() => onSelectConcept(c.name)}
                                title={isLocked ? `Complete the previous concept to unlock` : c.display_name}
                                className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-left text-sm transition-colors
                  ${isActive ? 'bg-[#6C63FF]/15 border border-[#6C63FF]/40' : 'border border-transparent hover:bg-[#1A1A2E]'}
                  ${isLocked ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                            >
                                <Icon size={16} color={color} className="shrink-0" />
                                <span className={`truncate ${isActive ? 'text-[#F1F5F9] font-semibold' : 'text-[#94A3B8]'}`}>
                                    {c.display_name}
                                </span>
                                {status === 'attempted' && (
                                    <span className="ml-auto text-[10px] text-[#F59E0B] font-mono">{state.attempts}</span>
                                )}
                            </button>
                        );
                    })}
                </div>
            </div>
        </aside>
    );
}