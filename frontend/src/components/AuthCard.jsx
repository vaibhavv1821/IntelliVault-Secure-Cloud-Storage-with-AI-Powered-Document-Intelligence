import React, { useState } from 'react';
import { ShieldCheck, LogIn, UserPlus, AlertCircle, Loader2 } from 'lucide-react';
import { loginApi, registerApi, setAuthToken } from '../services/api';

export const AuthCard = ({ onAuthSuccess }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    setSuccessMessage('');
    setLoading(true);

    try {
      if (isLogin) {
        const res = await loginApi(email, password);
        if (res.success && res.data?.token?.access_token) {
          setAuthToken(res.data.token.access_token);
          onAuthSuccess(res.data.user);
        } else {
          setErrorMessage(res.error?.message || 'Login failed. Please check your credentials.');
        }
      } else {
        const res = await registerApi(name, email, password);
        if (res.success) {
          setSuccessMessage('Account registered successfully! Logging you in...');
          // Automatically log in after registration
          const loginRes = await loginApi(email, password);
          if (loginRes.success && loginRes.data?.token?.access_token) {
            setAuthToken(loginRes.data.token.access_token);
            onAuthSuccess(loginRes.data.user);
          } else {
            setIsLogin(true);
          }
        } else {
          setErrorMessage(res.error?.message || 'Registration failed.');
        }
      }
    } catch (err) {
      setErrorMessage('A network error occurred. Please verify backend is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md w-full mx-auto p-8 rounded-2xl border border-slate-800 bg-slate-900/80 shadow-2xl backdrop-blur-md">
      {/* Header & Logo */}
      <div className="text-center mb-8">
        <div className="inline-flex p-3 bg-gradient-to-br from-teal-500 to-emerald-600 rounded-2xl shadow-lg shadow-teal-500/20 mb-3">
          <ShieldCheck className="w-8 h-8 text-slate-950" />
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-white">IntelliVault</h2>
        <p className="text-xs text-slate-400 mt-1">
          {isLogin ? 'Sign in to access your secure cloud vault' : 'Create an account with zero-knowledge encryption'}
        </p>
      </div>

      {/* Mode Switcher Tabs */}
      <div className="flex border border-slate-800 rounded-xl p-1 bg-slate-950/60 mb-6">
        <button
          type="button"
          onClick={() => { setIsLogin(true); setErrorMessage(''); }}
          className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all ${
            isLogin ? 'bg-teal-500 text-slate-950 shadow-md font-bold' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          Sign In
        </button>
        <button
          type="button"
          onClick={() => { setIsLogin(false); setErrorMessage(''); }}
          className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all ${
            !isLogin ? 'bg-teal-500 text-slate-950 shadow-md font-bold' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          Create Account
        </button>
      </div>

      {/* Feedback Messages */}
      {errorMessage && (
        <div className="p-3 mb-5 rounded-xl bg-red-950/40 border border-red-900/60 text-red-300 text-xs flex items-start gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{errorMessage}</span>
        </div>
      )}

      {successMessage && (
        <div className="p-3 mb-5 rounded-xl bg-emerald-950/40 border border-emerald-900/60 text-emerald-300 text-xs">
          {successMessage}
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        {!isLogin && (
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Display Name</label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Vaibhav"
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500"
            />
          </div>
        )}

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5">Email Address</label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="e.g. vaibhav@example.com"
            className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5">Password</label>
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder={isLogin ? 'Enter your password' : 'Min 8 chars, 1 upper, 1 digit, 1 special'}
            className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full mt-2 py-2.5 px-4 rounded-xl text-sm font-semibold bg-gradient-to-r from-teal-500 to-emerald-500 hover:from-teal-400 hover:to-emerald-400 text-slate-950 transition-all shadow-lg shadow-teal-500/20 active:scale-98 disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>{isLogin ? 'Signing In...' : 'Registering...'}</span>
            </>
          ) : isLogin ? (
            <>
              <LogIn className="w-4 h-4" />
              <span>Sign In</span>
            </>
          ) : (
            <>
              <UserPlus className="w-4 h-4" />
              <span>Register Account</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
};
