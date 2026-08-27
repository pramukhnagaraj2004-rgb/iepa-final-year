import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Navigate } from 'react-router-dom';

export default function Landing() {
  const { user, loading, API_BASE } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0A0A0F] text-[#6C63FF] font-bold">
        Loading IEPA Platform...
      </div>
    );
  }

  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleGoogleSignIn = () => {
    window.location.href = `${API_BASE}/auth/google`;
  };

  return (
    <div className="min-h-screen bg-[#0A0A0F] text-[#F1F5F9] flex flex-col justify-between">
      <header className="p-6 max-w-7xl mx-auto w-full flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-[#6C63FF] flex items-center justify-center font-black text-xl shadow-lg shadow-[#6C63FF]/30">
            IE
          </div>
          <span className="text-xl font-bold tracking-tight">IEPA</span>
        </div>
        <button
          onClick={handleGoogleSignIn}
          className="px-5 py-2.5 bg-[#6C63FF] hover:bg-[#5A52E8] transition-all font-semibold rounded-lg shadow-md text-sm"
        >
          Continue with Google
        </button>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-16 text-center space-y-8">
        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight leading-tight">
          Stop Googling your errors.<br />Start understanding them.
        </h1>
        <p className="max-w-2xl mx-auto text-lg text-[#94A3B8] leading-relaxed">
          Adaptive, ML-powered Python feedback that diagnoses the concept behind
          your bug — not just the error message.
        </p>

        <div className="pt-4 flex flex-col sm:flex-row gap-4 justify-center items-center">
          <button
            onClick={handleGoogleSignIn}
            className="w-full sm:w-auto px-8 py-4 bg-white hover:bg-slate-100 text-slate-900 font-bold rounded-xl shadow-xl transition-all flex items-center justify-center gap-3 text-base"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
            </svg>
            Continue with Google
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left pt-12">
          <div className="p-6 rounded-2xl bg-[#12121A] border border-[#2A2A3E] space-y-2">
            <h3 className="font-bold text-lg">Docker Sandbox</h3>
            <p className="text-sm text-[#94A3B8]">Runs your code in an isolated container and captures the real error.</p>
          </div>
          <div className="p-6 rounded-2xl bg-[#12121A] border border-[#2A2A3E] space-y-2">
            <h3 className="font-bold text-lg">ML Concept Mapping</h3>
            <p className="text-sm text-[#94A3B8]">TF-IDF & Logistic Regression classify the error into a concept gap.</p>
          </div>
          <div className="p-6 rounded-2xl bg-[#12121A] border border-[#2A2A3E] space-y-2">
            <h3 className="font-bold text-lg">Adaptive Curriculum</h3>
            <p className="text-sm text-[#94A3B8]">10 locked concepts you unlock one at a time by passing exercises.</p>
          </div>
        </div>
      </main>

      <footer className="p-6 text-center text-sm text-[#94A3B8] border-t border-[#2A2A3E]">
        Built for engineering students. Free to start.
      </footer>
    </div>
  );
}