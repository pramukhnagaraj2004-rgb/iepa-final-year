import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Navigate } from 'react-router-dom';

export default function Landing() {
  const { user, loading, API_BASE } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 text-indigo-600 font-bold">
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
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 text-white flex flex-col justify-between">
      {/* Navigation */}
      <header className="p-6 max-w-7xl mx-auto w-full flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center font-black text-xl shadow-lg shadow-indigo-500/30">
            IE
          </div>
          <span className="text-xl font-bold tracking-tight">IEPA Platform</span>
        </div>
        <button
          onClick={handleGoogleSignIn}
          className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 transition-all font-semibold rounded-lg shadow-md hover:shadow-indigo-500/25 flex items-center gap-2 text-sm"
        >
          Sign In
        </button>
      </header>

      {/* Hero Content */}
      <main className="max-w-5xl mx-auto px-6 py-16 text-center space-y-8">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-400/20 text-indigo-300 text-sm font-medium">
          <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
          Machine Learning Powered Pedagogical Diagnostics
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight leading-tight sm:leading-none bg-gradient-to-r from-white via-indigo-100 to-indigo-300 bg-clip-text text-transparent">
          Intelligent Error Pattern Analyzer for Programming Learners
        </h1>

        <p className="max-w-2xl mx-auto text-lg text-slate-300 leading-relaxed">
          Execute code in secure isolated sandboxes, automatically classify conceptual misconceptions with custom TF-IDF & Logistic Regression classifiers, and receive adaptive tier-based feedback.
        </p>

        {/* CTA Section */}
        <div className="pt-4 flex flex-col sm:flex-row gap-4 justify-center items-center">
          <button
            onClick={handleGoogleSignIn}
            className="w-full sm:w-auto px-8 py-4 bg-white hover:bg-slate-100 text-slate-900 font-bold rounded-xl shadow-xl transition-all transform hover:-translate-y-0.5 flex items-center justify-center gap-3 text-base"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
              />
            </svg>
            Continue with Google
          </button>
        </div>

        {/* Features Highlights */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left pt-12">
          <div className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-sm space-y-2">
            <div className="text-2xl">⚡</div>
            <h3 className="font-bold text-lg text-white">Docker Isolated Execution</h3>
            <p className="text-sm text-slate-300">Safely runs untrusted code under 128MB RAM, 0.5 CPU, and a strict 10-second timeout.</p>
          </div>
          <div className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-sm space-y-2">
            <div className="text-2xl">🧠</div>
            <h3 className="font-bold text-lg text-white">Concept Gap Mapping</h3>
            <p className="text-sm text-slate-300">Custom TF-IDF & One-vs-Rest ML models classify errors into 10 pedagogical categories.</p>
          </div>
          <div className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-sm space-y-2">
            <div className="text-2xl">📈</div>
            <h3 className="font-bold text-lg text-white">Mastery Tracking</h3>
            <p className="text-sm text-slate-300">Rule-based Bayesian decision engine personalizes feedback across Hint, Explain, and Exercise tiers.</p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="p-6 text-center text-sm text-slate-400 border-t border-white/5">
        IEPA Final Year Project &copy; 2026. Built with Python 3.11, FastAPI, React, and MongoDB Atlas.
      </footer>
    </div>
  );
}
