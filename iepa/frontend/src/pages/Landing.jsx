import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Navigate } from 'react-router-dom';
import { Sun, Moon, Container, GitBranch, Lock, ArrowRight } from 'lucide-react';

export default function Landing() {
  const { user, loading, API_BASE } = useAuth();
  const [theme, setTheme] = useState('dark');
  const isDark = theme === 'dark';

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0A0A0F] text-[#6C63FF] font-bold">
        Loading IEPA Platform...
      </div>
    );
  }
  if (user) return <Navigate to="/dashboard" replace />;

  const handleGoogleSignIn = () => {
    window.location.href = `${API_BASE}/auth/google`;
  };

  const c = isDark
    ? {
      bg: '#0A0A0F', surface: '#12121A', surfaceAlt: '#1A1A2E', border: '#2A2A3E',
      text: '#F1F5F9', textSub: '#94A3B8', navBg: '#0A0A0Fcc', codeBg: '#0d0d14',
      ctaBg: '#0A0A0F', ctaText: '#F1F5F9', barTrack: '#2A2A3E',
    }
    : {
      bg: '#FFFFFF', surface: '#F8FAFC', surfaceAlt: '#FFFFFF', border: '#E2E8F0',
      text: '#0F172A', textSub: '#64748B', navBg: '#FFFFFFcc', codeBg: '#0d0d14',
      ctaBg: '#0A0A0F', ctaText: '#F1F5F9', barTrack: '#E2E8F0',
    };

  const primary = '#6C63FF';

  const features = [
    { icon: Container, title: 'Docker Sandbox', desc: 'Runs your code in an isolated container and captures the real error safely.' },
    { icon: GitBranch, title: 'ML Concept Mapping', desc: "TF-IDF & Logistic Regression classify the error signature into a distinct concept gap." },
    { icon: Lock, title: 'Adaptive Curriculum', desc: '10 locked concepts you unlock one at a time by passing structured exercises.' },
  ];

  const steps = [
    { step: 'STEP 01', title: 'Run isolated code', desc: 'Submit your code directly inside the sandbox container for verification.' },
    { step: 'STEP 02', title: 'Classify conceptual gap', desc: 'Our models map runtime error traces to logical paradigms instantly.' },
    { step: 'STEP 03', title: 'Adapt exercise paths', desc: 'Unlock customized conceptual review challenges to lock in your logic.' },
  ];

  const milestones = [
    { name: 'Edge Case Validation', locked: false },
    { name: 'Off-By-One Logic', locked: true },
    { name: 'Immutable Datatypes', locked: true },
    { name: 'Scope Resolution', locked: true },
  ];

  return (
    <div style={{ backgroundColor: c.bg, color: c.text }} className="min-h-screen transition-colors duration-300">
      {/* NAV */}
      <header
        style={{ backgroundColor: c.navBg, borderColor: c.border }}
        className="sticky top-0 z-50 backdrop-blur-md border-b flex items-center justify-between px-8 h-16"
      >
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-[#6C63FF] flex items-center justify-center font-black text-sm text-white">IE</div>
          <span className="font-bold tracking-tight">IEPA</span>
        </div>
        <nav className="hidden md:flex items-center gap-8 text-sm font-medium" style={{ color: c.textSub }}>
          <a href="#features" className="hover:text-[#6C63FF] transition-colors">Features</a>
          <a href="#demo" className="hover:text-[#6C63FF] transition-colors">Interactive Demo</a>
          <a href="#sandbox" className="hover:text-[#6C63FF] transition-colors">Sandbox</a>
          <a href="#curriculum" className="hover:text-[#6C63FF] transition-colors">Curriculum</a>
        </nav>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setTheme(isDark ? 'light' : 'dark')}
            style={{ borderColor: c.border }}
            className="w-9 h-9 rounded-lg border flex items-center justify-center hover:border-[#6C63FF] transition-colors"
            aria-label="Toggle theme"
          >
            {isDark ? <Sun size={16} color={c.textSub} /> : <Moon size={16} color={c.textSub} />}
          </button>
          <button onClick={handleGoogleSignIn} className="text-sm font-semibold hover:text-[#6C63FF] transition-colors" style={{ color: c.textSub }}>
            Sign In
          </button>
          <button
            onClick={handleGoogleSignIn}
            style={{ backgroundColor: isDark ? '#FFFFFF' : '#0A0A0F', color: isDark ? '#0A0A0F' : '#FFFFFF' }}
            className="px-4 py-2 rounded-lg text-sm font-bold transition-transform hover:scale-105"
          >
            Launch App
          </button>
        </div>
      </header>

      {/* HERO */}
      <section className="max-w-5xl mx-auto px-6 pt-20 pb-16 text-center">
        <span
          style={{ borderColor: c.border, color: primary }}
          className="inline-block px-3 py-1 rounded-full border text-[10px] font-bold uppercase tracking-wider mb-6"
        >
          Concept-Based Python Debugging
        </span>
        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight leading-tight mb-6">
          Stop Googling your errors.<br />Start understanding them.
        </h1>
        <p className="max-w-2xl mx-auto text-lg mb-8" style={{ color: c.textSub }}>
          Adaptive, ML-powered Python feedback that diagnoses the concept behind your bug —
          not just the error message. Custom-built for engineering students.
        </p>
        <button
          onClick={handleGoogleSignIn}
          className="px-8 py-4 bg-white hover:bg-slate-100 text-slate-900 font-bold rounded-xl shadow-xl transition-all inline-flex items-center gap-3 text-base border border-slate-200"
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
          </svg>
          Continue with Google
        </button>
        <p className="text-xs mt-3" style={{ color: c.textSub }}>Instant student account · Free to start</p>

        {/* Demo panel */}
        <div id="demo" style={{ backgroundColor: c.codeBg, borderColor: c.border }} className="mt-14 rounded-2xl border overflow-hidden text-left shadow-2xl">
          <div className="flex items-center justify-between px-4 py-2.5" style={{ backgroundColor: '#141420', borderBottom: `1px solid ${c.border}` }}>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-[#EF4444]" />
              <span className="w-2.5 h-2.5 rounded-full bg-[#F59E0B]" />
              <span className="w-2.5 h-2.5 rounded-full bg-[#10B981]" />
              <span className="ml-3 text-xs text-[#94A3B8] font-mono">sandbox_run_active.py</span>
            </div>
            <span className="px-2 py-0.5 rounded bg-[#10B981]/15 text-[#10B981] text-[10px] font-bold uppercase">ML Classifier Ready</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-0">
            <div className="p-5 font-mono text-sm leading-relaxed">
              <div><span className="text-[#6C63FF]">def</span> <span className="text-[#F1F5F9]">calculate_average(grades):</span></div>
              <div className="pl-4 text-[#F1F5F9]">total = <span className="text-[#F59E0B]">sum</span>(grades)</div>
              <div className="pl-4 text-[#F1F5F9]">count = <span className="text-[#F59E0B]">len</span>(grades)</div>
              <div className="pl-4 text-[#F1F5F9]">return total / count</div>
              <div className="mt-3 text-[#94A3B8]"># Executing with empty list</div>
              <div className="text-[#F1F5F9]">calculate_average([])</div>
            </div>
            <div className="p-5 border-t md:border-t-0 md:border-l space-y-3" style={{ borderColor: c.border }}>
              <div className="flex items-center gap-2 text-[#EF4444] text-xs font-bold uppercase">
                ⚠ Concept Gap Detected
              </div>
              <div className="font-mono text-sm text-[#EF4444]">ZeroDivisionError: division by zero</div>
              <div className="font-mono text-xs text-[#10B981]">Concept → Edge Case Validation</div>
              <p className="text-sm text-[#F1F5F9] leading-relaxed">
                Your function doesn't check if the 'grades' list is empty. An empty list makes 'count' 0, leading to a division error.
              </p>
              <div className="text-[#6C63FF] text-xs font-bold pt-1">View Concept Exercise Path →</div>
            </div>
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section id="features" className="max-w-5xl mx-auto px-6 py-20 text-center">
        <span style={{ color: primary }} className="text-xs font-bold uppercase tracking-wider">How We Accelerate Engineering Education</span>
        <h2 className="text-3xl sm:text-4xl font-extrabold mt-3 mb-12">Conceptual debugging, automated.</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
          {features.map((f) => (
            <div key={f.title} style={{ backgroundColor: c.surface, borderColor: c.border }} className="p-6 rounded-2xl border space-y-3">
              <div className="w-9 h-9 rounded-lg bg-[#6C63FF]/15 flex items-center justify-center">
                <f.icon size={18} color={primary} />
              </div>
              <h3 className="font-bold text-lg">{f.title}</h3>
              <p className="text-sm" style={{ color: c.textSub }}>{f.desc}</p>
              <div className="text-xs font-bold pt-1" style={{ color: primary }}>Learn how it works →</div>
            </div>
          ))}
        </div>
      </section>

      {/* PROCESS */}
      <section style={{ backgroundColor: c.surface }} className="py-20">
        <div className="max-w-5xl mx-auto px-6 text-center">
          <span style={{ color: primary }} className="text-xs font-bold uppercase tracking-wider">Diagnostic Process</span>
          <h2 className="text-3xl sm:text-4xl font-extrabold mt-3 mb-12">From traceback to mental model.</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
            {steps.map((s) => (
              <div key={s.step} style={{ backgroundColor: c.surfaceAlt, borderColor: c.border }} className="p-6 rounded-2xl border space-y-2">
                <span style={{ color: primary }} className="text-[10px] font-bold uppercase tracking-wider">{s.step}</span>
                <h3 className="font-bold text-lg">{s.title}</h3>
                <p className="text-sm" style={{ color: c.textSub }}>{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CURRICULUM / MILESTONES */}
      <section id="curriculum" className="max-w-5xl mx-auto px-6 py-20">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-10 items-start">
          <div>
            <span style={{ color: primary }} className="text-xs font-bold uppercase tracking-wider">Adaptive Curriculum</span>
            <h2 className="text-3xl sm:text-4xl font-extrabold mt-3 mb-4 leading-tight">
              10 Concept Milestones.<br />Unlock your full potential.
            </h2>
            <p className="mb-6" style={{ color: c.textSub }}>
              Instead of giving you direct answers, IEPA identifies the concepts you are failing to grasp
              and unlocks matching exercises to bridge the gaps. Complete exercises to earn your concept certificates.
            </p>
            <div className="space-y-2">
              {milestones.map((m) => (
                <div key={m.name} className="flex items-center gap-2 text-sm font-semibold">
                  <Lock size={14} color={m.locked ? c.textSub : primary} />
                  <span style={{ color: m.locked ? c.textSub : c.text }}>{m.name}</span>
                </div>
              ))}
            </div>
          </div>

          <div id="sandbox" style={{ backgroundColor: c.surface, borderColor: c.border }} className="p-6 rounded-2xl border">
            <span className="text-xs font-bold uppercase tracking-wider" style={{ color: primary }}>Student Metrics</span>
            <div className="flex items-end gap-3 h-24 mt-4 mb-4">
              <div style={{ backgroundColor: c.barTrack }} className="w-16 h-10 rounded-lg" />
              <div style={{ backgroundColor: c.barTrack }} className="w-16 h-16 rounded-lg" />
              <div className="w-16 h-24 rounded-lg" style={{ backgroundColor: primary }} />
            </div>
            <p className="text-sm" style={{ color: c.textSub }}>
              Passing rate increases by up to <strong style={{ color: c.text }}>47%</strong> when students debug
              conceptually rather than guessing code changes.
            </p>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section style={{ backgroundColor: c.ctaBg, color: c.ctaText }} className="py-20 text-center">
        <h2 className="text-3xl sm:text-4xl font-extrabold mb-4">Concept gaps shouldn't stop your compilation.</h2>
        <p className="max-w-xl mx-auto mb-8 text-[#94A3B8]">
          Join thousands of engineering students mastering Python diagnostic concepts. Safe sandbox environments, automatic diagnostic logging.
        </p>
        <button
          onClick={handleGoogleSignIn}
          className="px-8 py-4 bg-white hover:bg-slate-100 text-slate-900 font-bold rounded-xl shadow-xl transition-all inline-flex items-center gap-2"
        >
          Continue with Google <ArrowRight size={16} />
        </button>
      </section>

      {/* FOOTER */}
      <footer style={{ borderColor: c.border }} className="border-t py-6 px-8 flex flex-col sm:flex-row justify-between items-center gap-2 text-xs" >
        <span style={{ color: c.textSub }}>Built for engineering students. Free to start.</span>
        <span style={{ color: c.textSub }}>© 2026 IEPA. Developed for Educational Sandbox environments.</span>
      </footer>
    </div>
  );
}