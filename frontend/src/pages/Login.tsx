import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield,
  Eye,
  EyeOff,
  Check,
  KeyRound,
  X,
  Cpu,
  Fingerprint,
  Mail,
  User as UserIcon,
  ArrowRight
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { authApi } from '../services/api';
import toast from 'react-hot-toast';

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, register, loginWithGoogle, isAuthenticated } = useAuth();

  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [role, setRole] = useState('Security Analyst');
  const [rememberMe, setRememberMe] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);

  // Google Sign-In custom modal state
  const [googleModalOpen, setGoogleModalOpen] = useState(false);
  const [customGoogleEmail, setCustomGoogleEmail] = useState('');
  const [customGoogleName, setCustomGoogleName] = useState('');

  // Forgot password modal state
  const [forgotModalOpen, setForgotModalOpen] = useState(false);
  const [forgotEmail, setForgotEmail] = useState('');
  const [forgotLoading, setForgotLoading] = useState(false);

  const from = (location.state as any)?.from?.pathname || '/';

  // If already authenticated, redirect
  useEffect(() => {
    if (isAuthenticated) {
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, from]);

  // Attempt standard Google Identity Services initialization if Client ID present
  useEffect(() => {
    try {
      const googleClientId = (import.meta as any).env?.VITE_GOOGLE_CLIENT_ID;
      if (googleClientId && (window as any).google?.accounts?.id) {
        (window as any).google.accounts.id.initialize({
          client_id: googleClientId,
          callback: async (response: any) => {
            if (response?.credential) {
              setGoogleLoading(true);
              try {
                const ok = await loginWithGoogle({ credential: response.credential });
                if (ok) navigate(from, { replace: true });
              } finally {
                setGoogleLoading(false);
              }
            }
          },
        });
      }
    } catch {}
  }, [loginWithGoogle, navigate, from]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      toast.error('Please fill in all required credentials.');
      return;
    }

    setLoading(true);
    try {
      if (mode === 'login') {
        const success = await login(email, password, rememberMe);
        if (success) {
          navigate(from, { replace: true });
        }
      } else {
        if (!name.trim()) {
          toast.error('Please enter your full name for node clearance.');
          setLoading(false);
          return;
        }
        const success = await register(email, password, name, role);
        if (success) {
          navigate(from, { replace: true });
        }
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleButtonClick = () => {
    const googleClientId = (import.meta as any).env?.VITE_GOOGLE_CLIENT_ID;
    if (googleClientId && (window as any).google?.accounts?.id) {
      try {
        (window as any).google.accounts.id.prompt();
        return;
      } catch {}
    }
    // Open Google Account dialog to allow direct Gmail sign-in
    setGoogleModalOpen(true);
  };

  const handleCustomGoogleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customGoogleEmail) {
      toast.error('Please enter your Google / Gmail address');
      return;
    }

    setGoogleLoading(true);
    try {
      const gName = customGoogleName.trim() || customGoogleEmail.split('@')[0];
      const ok = await loginWithGoogle({
        email: customGoogleEmail,
        name: gName,
      });
      if (ok) {
        setGoogleModalOpen(false);
        navigate(from, { replace: true });
      }
    } finally {
      setGoogleLoading(false);
    }
  };

  const handleForgotPasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!forgotEmail) {
      toast.error('Please specify your registered security email.');
      return;
    }
    setForgotLoading(true);
    try {
      const res = await authApi.forgotPassword({ email: forgotEmail });
      toast.success(res.data?.message || 'Password reset link dispatched!');
      setForgotModalOpen(false);
      setForgotEmail('');
    } catch {
      toast.error('Could not send reset link. Please check the email.');
    } finally {
      setForgotLoading(false);
    }
  };

  const fillDemo = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    if (mode === 'register') setMode('login');
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-gradient-to-br from-[#1b64da] via-[#3b82f6] to-[#60a5fa] p-4 sm:p-6 lg:p-8 font-sans selection:bg-blue-600 selection:text-white relative overflow-hidden">
      {/* Ambient background glow elements */}
      <div className="absolute -top-32 -left-32 w-96 h-96 bg-white/20 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-32 -right-32 w-96 h-96 bg-blue-900/30 rounded-full blur-3xl pointer-events-none" />

      {/* Main card container */}
      <motion.div
        initial={{ opacity: 0, scale: 0.96, y: 15 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
        className="w-full max-w-[1040px] bg-white rounded-[32px] shadow-[0_25px_70px_rgba(0,35,100,0.22)] border border-white/60 p-4 sm:p-5 lg:p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-8 relative z-10"
      >
        {/* LEFT PANEL - Electric Blue Shield Hero Card */}
        <div className="lg:col-span-5 bg-gradient-to-b from-[#2f77f5] via-[#2065e8] to-[#1253d2] rounded-[24px] p-6 sm:p-8 flex flex-col justify-between items-center text-white relative overflow-hidden shadow-inner min-h-[360px] lg:min-h-[580px]">
          {/* Subtle background tech rings */}
          <div className="absolute inset-0 opacity-15 pointer-events-none">
            <div className="absolute -top-12 -left-12 w-64 h-64 rounded-full border border-white/30" />
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-80 h-80 rounded-full border border-white/20" />
            <div className="absolute -bottom-16 -right-16 w-72 h-72 rounded-full border border-white/30" />
          </div>

          {/* Top telemetry tag */}
          <div className="w-full flex items-center justify-between text-xs tracking-wider font-medium text-blue-100/90 uppercase">
            <div className="flex items-center gap-1.5 bg-white/15 backdrop-blur-md px-3 py-1 rounded-full border border-white/20">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>Node 09 • Online</span>
            </div>
            <div className="text-[11px] font-mono opacity-80 flex items-center gap-1">
              <Fingerprint className="w-3.5 h-3.5" />
              <span>256-BIT</span>
            </div>
          </div>

          {/* Center Graphic: RansomGuard / Cyber Shield Logo */}
          <div className="my-auto py-8 flex flex-col items-center justify-center relative">
            <motion.div
              animate={{ y: [-4, 4, -4] }}
              transition={{ repeat: Infinity, duration: 5, ease: 'easeInOut' }}
              className="relative"
            >
              {/* Shield container */}
              <div className="w-40 h-48 sm:w-48 sm:h-56 relative flex items-center justify-center">
                <svg
                  viewBox="0 0 200 240"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                  className="w-full h-full drop-shadow-[0_12px_24px_rgba(0,0,0,0.18)]"
                >
                  <path
                    d="M100 12 L175 45 C175 140 140 195 100 228 C60 195 25 140 25 45 Z"
                    fill="white"
                  />
                  <path
                    d="M100 36 L158 62 C158 135 130 178 100 205 C70 178 42 135 42 62 Z"
                    fill="#2065e8"
                  />
                  <path
                    d="M72 75 L86 75 L114 135 L114 75 L128 75 L128 165 L114 165 L86 105 L86 165 L72 165 Z"
                    fill="white"
                  />
                  <circle cx="100" cy="52" r="3" fill="#60a5fa" />
                  <circle cx="100" cy="188" r="3" fill="#60a5fa" />
                </svg>
              </div>
            </motion.div>

            <h2 className="text-xl font-bold tracking-tight text-white mt-4 text-center">
              Autonomous Ransomware Shield
            </h2>
            <p className="text-xs text-blue-100 text-center max-w-[240px] mt-1 opacity-90 leading-relaxed">
              Real-time heuristic behavioral surveillance & ML threat quarantine.
            </p>
          </div>

          {/* Bottom security badges */}
          <div className="w-full pt-4 border-t border-white/15 flex items-center justify-between text-[11px] text-blue-100/80">
            <div className="flex items-center gap-1">
              <Cpu className="w-3.5 h-3.5 text-blue-200" />
              <span>Engine v1.0</span>
            </div>
            <div className="flex items-center gap-1">
              <Shield className="w-3.5 h-3.5 text-emerald-300" />
              <span>SOC-2 Certified</span>
            </div>
          </div>
        </div>

        {/* RIGHT PANEL - Authentication Form */}
        <div className="lg:col-span-7 flex flex-col justify-between px-2 sm:px-6 py-4 sm:py-6">
          {/* Brand Header */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-600">
                  <Shield className="w-5 h-5 fill-blue-600/20" />
                </div>
                <div>
                  <span className="font-extrabold text-slate-800 tracking-wider text-sm flex items-center gap-1">
                    RANSOMGUARD <span className="text-blue-600 font-black">NODE</span>
                  </span>
                  <p className="text-[10px] font-medium text-slate-400 -mt-0.5 tracking-wide">
                    Protecting the Cyberspace
                  </p>
                </div>
              </div>

              {/* Mode switch button */}
              <button
                type="button"
                onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
                className="text-xs font-semibold text-blue-600 hover:text-blue-700 bg-blue-50 hover:bg-blue-100/80 px-3 py-1.5 rounded-full transition-colors duration-150"
              >
                {mode === 'login' ? 'Create Account' : 'Back to Login'}
              </button>
            </div>

            {/* Title */}
            <div className="text-center my-4">
              <h1 className="text-2xl sm:text-3xl font-bold text-blue-600 tracking-tight">
                {mode === 'login' ? 'Sign in to RansomGuard Node' : 'Register Security Node'}
              </h1>
              <p className="text-xs text-slate-500 mt-1">
                {mode === 'login'
                  ? 'Enter your verified credentials to access live surveillance'
                  : 'Provision a new security analyst access key'}
              </p>
            </div>

            {/* Google SSO Button */}
            <div className="flex flex-col items-center justify-center mt-3 mb-4">
              <button
                type="button"
                onClick={handleGoogleButtonClick}
                disabled={googleLoading || loading}
                className="w-12 h-12 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 flex items-center justify-center transition-all duration-200 shadow-sm hover:shadow hover:scale-105 active:scale-95 group relative"
                title="Sign in with Google / Gmail"
              >
                {googleLoading ? (
                  <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                ) : (
                  <svg className="w-5 h-5" viewBox="0 0 24 24">
                    <path
                      fill="#4285F4"
                      d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.66-5.17 3.66-9.17z"
                    />
                    <path
                      fill="#34A853"
                      d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.33 24 12 24z"
                    />
                    <path
                      fill="#FBBC05"
                      d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 9.99 0 12s.45 3.82 1.25 5.42l4.03-3.15z"
                    />
                    <path
                      fill="#EA4335"
                      d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98z"
                    />
                  </svg>
                )}
              </button>
              <span className="text-[10px] text-slate-400 mt-1 font-medium">Click to sign in with your Google / Gmail</span>
            </div>

            {/* Divider */}
            <div className="relative flex items-center justify-center my-4">
              <div className="border-t border-slate-200 w-3/4" />
              <span className="bg-white px-3 text-xs text-slate-400 font-medium absolute">
                or
              </span>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-3.5">
              {mode === 'register' && (
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700 block">
                    Full Name
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      required
                      placeholder="enter your full name"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-white text-slate-800 text-sm placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all duration-150 outline-none"
                    />
                  </div>
                </div>
              )}

              {/* Email */}
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700 block">
                  E-mail
                </label>
                <div className="relative">
                  <input
                    type="email"
                    required
                    placeholder="enter your email address"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-white text-slate-800 text-sm placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all duration-150 outline-none"
                  />
                </div>
              </div>

              {/* Password */}
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700 block">
                  Password
                </label>
                <div className="relative flex items-center">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    placeholder="enter your password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-4 py-2.5 pr-11 rounded-xl border border-slate-200 bg-white text-slate-800 text-sm placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all duration-150 outline-none"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 text-slate-400 hover:text-slate-600 p-1"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Register Role Select */}
              {mode === 'register' && (
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700 block">
                    Assigned Role
                  </label>
                  <select
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-white text-slate-800 text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-100 outline-none"
                  >
                    <option value="Security Analyst">Security Analyst</option>
                    <option value="Security Admin">Security Admin</option>
                    <option value="SOC Incident Responder">SOC Incident Responder</option>
                  </select>
                </div>
              )}

              {/* Options Row (Keep signed in / Forgot password) */}
              <div className="flex items-center justify-between pt-1">
                <label className="flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="sr-only"
                  />
                  <div
                    className={`w-4 h-4 rounded flex items-center justify-center transition-colors ${
                      rememberMe ? 'bg-blue-600 text-white' : 'border border-slate-300 bg-white'
                    }`}
                  >
                    {rememberMe && <Check className="w-3 h-3 stroke-[3]" />}
                  </div>
                  <span className="text-xs text-slate-600 font-medium">Keep me signed in</span>
                </label>

                {mode === 'login' && (
                  <button
                    type="button"
                    onClick={() => setForgotModalOpen(true)}
                    className="text-xs font-semibold text-blue-600 hover:text-blue-700 transition-colors"
                  >
                    Forgot Password?
                  </button>
                )}
              </div>

              {/* Primary Submit Button */}
              <motion.button
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
                type="submit"
                disabled={loading || googleLoading}
                className="w-full mt-2 py-3 px-4 rounded-xl bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-700 hover:to-blue-600 text-white font-semibold text-sm shadow-md shadow-blue-500/25 transition-all duration-200 flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Authenticating Node...</span>
                  </>
                ) : (
                  <span>{mode === 'login' ? 'Sign In' : 'Complete Registration'}</span>
                )}
              </motion.button>
            </form>
          </div>

          {/* Quick Demo Credentials Footer Helper */}
          <div className="mt-5 pt-4 border-t border-slate-100 flex flex-col items-center">
            <div className="text-[11px] text-slate-400 mb-1.5 font-medium flex items-center gap-1">
              <KeyRound className="w-3 h-3 text-slate-400" />
              <span>Quick Test Credentials (1-Click Fill):</span>
            </div>
            <div className="flex flex-wrap items-center justify-center gap-2">
              <button
                type="button"
                onClick={() => fillDemo('admin@ransomguard.io', 'admin123')}
                className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-blue-50 hover:text-blue-700 text-slate-600 border border-slate-200 transition-colors"
              >
                Admin (admin@ransomguard.io)
              </button>
              <button
                type="button"
                onClick={() => fillDemo('analyst@ransomguard.io', 'analyst123')}
                className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-blue-50 hover:text-blue-700 text-slate-600 border border-slate-200 transition-colors"
              >
                Analyst (analyst@ransomguard.io)
              </button>
            </div>

            <p className="text-[11px] text-slate-400 mt-4">
              &copy; {new Date().getFullYear()} RansomGuard Security. All rights reserved.
            </p>
          </div>
        </div>
      </motion.div>

      {/* Direct Google Account Sign-In Modal */}
      <AnimatePresence>
        {googleModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 backdrop-blur-sm p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              className="bg-white rounded-3xl max-w-md w-full p-6 sm:p-7 shadow-2xl border border-slate-100 relative"
            >
              <button
                onClick={() => setGoogleModalOpen(false)}
                className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 p-1.5 rounded-full hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>

              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 rounded-2xl border border-slate-200 bg-white flex items-center justify-center shadow-sm">
                  <svg className="w-6 h-6" viewBox="0 0 24 24">
                    <path
                      fill="#4285F4"
                      d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.66-5.17 3.66-9.17z"
                    />
                    <path
                      fill="#34A853"
                      d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.33 24 12 24z"
                    />
                    <path
                      fill="#FBBC05"
                      d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 9.99 0 12s.45 3.82 1.25 5.42l4.03-3.15z"
                    />
                    <path
                      fill="#EA4335"
                      d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98z"
                    />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-bold text-slate-800">Sign in with Google</h3>
                  <p className="text-xs text-slate-500">
                    Connect your Gmail to initialize your RansomGuard session
                  </p>
                </div>
              </div>

              <form onSubmit={handleCustomGoogleSubmit} className="space-y-3.5 mt-2">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
                    <Mail className="w-3.5 h-3.5 text-blue-600" />
                    <span>Your Gmail Address</span>
                  </label>
                  <input
                    type="email"
                    required
                    placeholder="e.g. yourname@gmail.com"
                    value={customGoogleEmail}
                    onChange={(e) => setCustomGoogleEmail(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-100 outline-none"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
                    <UserIcon className="w-3.5 h-3.5 text-blue-600" />
                    <span>Your Name (Optional)</span>
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. John Doe"
                    value={customGoogleName}
                    onChange={(e) => setCustomGoogleName(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-100 outline-none"
                  />
                </div>

                <div className="flex gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setGoogleModalOpen(false)}
                    className="w-1/3 py-2.5 rounded-xl border border-slate-200 text-slate-600 text-xs font-semibold hover:bg-slate-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={googleLoading}
                    className="w-2/3 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-md shadow-blue-500/20 flex items-center justify-center gap-2"
                  >
                    {googleLoading ? (
                      <span>Connecting...</span>
                    ) : (
                      <>
                        <span>Continue with Google</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </>
                    )}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Forgot Password Modal */}
      <AnimatePresence>
        {forgotModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 backdrop-blur-sm p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-100 relative"
            >
              <button
                onClick={() => setForgotModalOpen(false)}
                className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 p-1"
              >
                <X className="w-5 h-5" />
              </button>

              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
                  <KeyRound className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-slate-800">Reset Password</h3>
                  <p className="text-xs text-slate-500">
                    Enter your security clearance email to receive reset instructions
                  </p>
                </div>
              </div>

              <form onSubmit={handleForgotPasswordSubmit} className="space-y-4 mt-4">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700">Security Email</label>
                  <input
                    type="email"
                    required
                    placeholder="e.g. admin@ransomguard.io"
                    value={forgotEmail}
                    onChange={(e) => setForgotEmail(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-100 outline-none"
                  />
                </div>

                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setForgotModalOpen(false)}
                    className="w-1/2 py-2.5 rounded-xl border border-slate-200 text-slate-600 text-xs font-semibold hover:bg-slate-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={forgotLoading}
                    className="w-1/2 py-2.5 rounded-xl bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 disabled:opacity-50"
                  >
                    {forgotLoading ? 'Sending...' : 'Send Reset Link'}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Login;
