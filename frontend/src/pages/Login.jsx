import React, { useState } from 'react';
import { 
  HeartPulse, 
  Lock, 
  Mail, 
  Shield, 
  Stethoscope, 
  Activity, 
  ArrowRight, 
  ShieldCheck, 
  KeyRound, 
  CheckCircle2, 
  AlertCircle 
} from 'lucide-react';
import { GradientMesh, Button, Input } from '../components/ui';
import { useAuth, DEMO_PROFILES } from '../context/AuthContext';

export const Login = ({ onLoginSuccess }) => {
  const { login } = useAuth();
  const [selectedRole, setSelectedRole] = useState('doctor');
  const [email, setEmail] = useState(DEMO_PROFILES.doctor.email);
  const [password, setPassword] = useState(DEMO_PROFILES.doctor.defaultPassword);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  const handleRoleChange = (role) => {
    setSelectedRole(role);
    setErrorMsg(null);
    if (DEMO_PROFILES[role]) {
      setEmail(DEMO_PROFILES[role].email);
      setPassword(DEMO_PROFILES[role].defaultPassword);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);

    try {
      await login(email, password, selectedRole);
      setLoading(false);
      onLoginSuccess?.();
    } catch (err) {
      setLoading(false);
      setErrorMsg('Authentication failed. Please verify clinical staff credentials.');
    }
  };

  const handleQuickLogin = async (role) => {
    setSelectedRole(role);
    setErrorMsg(null);
    const profile = DEMO_PROFILES[role];
    setEmail(profile.email);
    setPassword(profile.defaultPassword);
    setLoading(true);
    try {
      await login(profile.email, profile.defaultPassword, role);
      setLoading(false);
      onLoginSuccess?.();
    } catch (err) {
      setLoading(false);
      setErrorMsg('Login failed.');
    }
  };

  const activeProfile = DEMO_PROFILES[selectedRole];

  return (
    <GradientMesh className="flex items-center justify-center min-h-screen p-4">
      <div className="w-full max-w-lg">
        {/* Glass Card Container */}
        <div className="glass-panel rounded-3xl p-8 sm:p-10 shadow-[0_20px_50px_rgba(0,0,0,0.08)] border border-white/60 relative overflow-hidden backdrop-blur-xl">
          {/* Subtle Glow Accent */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-48 h-1 bg-gradient-to-r from-transparent via-[#0EA5B7] to-transparent" />

          {/* Logo Mark */}
          <div className="flex flex-col items-center text-center mb-6">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-[#0D8A9A] to-[#0EA5B7] flex items-center justify-center text-white shadow-lg shadow-teal-500/25 mb-3.5 transition-transform hover:scale-105 duration-200">
              <HeartPulse className="w-8 h-8 animate-pulse" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">PulseGuard-AI</h1>
            <p className="text-xs text-slate-500 mt-1 max-w-sm">
              Role-Based Access Control • Distinct Panel Authorization
            </p>
          </div>

          {/* Panel Selector: Segmented Control */}
          <div className="mb-5">
            <label className="block text-xs font-semibold text-slate-700 mb-2">
              Select Panel & Clinical Role
            </label>
            <div className="grid grid-cols-2 gap-2 bg-slate-100/90 p-1.5 rounded-2xl border border-slate-200/60">
              <button
                type="button"
                onClick={() => handleRoleChange('doctor')}
                className={`py-2 px-2 text-xs font-bold rounded-xl transition-all duration-200 flex flex-col items-center gap-1 ${
                  selectedRole === 'doctor'
                    ? 'bg-white text-[#0D8A9A] shadow-sm shadow-slate-200'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                <Stethoscope className="w-4 h-4" />
                Doctor Panel
              </button>

              <button
                type="button"
                onClick={() => handleRoleChange('admin')}
                className={`py-2 px-2 text-xs font-bold rounded-xl transition-all duration-200 flex flex-col items-center gap-1 ${
                  selectedRole === 'admin'
                    ? 'bg-white text-purple-700 shadow-sm shadow-slate-200'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                <Shield className="w-4 h-4" />
                Admin Panel
              </button>
            </div>
          </div>

          {/* Panel Scope & Isolation Description */}
          <div className="mb-5 p-3 rounded-2xl bg-slate-50/80 border border-slate-200/80 text-xs">
            <div className="flex items-center justify-between font-semibold text-slate-800 mb-1">
              <span>{activeProfile.name}</span>
              <span className="font-mono text-[10px] uppercase text-teal-700 font-bold bg-teal-50 px-2 py-0.5 rounded border border-teal-200">
                {selectedRole.toUpperCase()} CLEARANCE
              </span>
            </div>
            <p className="text-[11px] text-slate-500 leading-relaxed">
              {activeProfile.description}
            </p>
          </div>

          {errorMsg && (
            <div className="mb-4 p-3 rounded-xl bg-red-50 border border-red-200 text-xs text-red-700 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Staff Email"
              type="email"
              icon={Mail}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />

            <Input
              label="Clinical Passkey / Password"
              type="password"
              icon={Lock}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

            <Button
              type="submit"
              variant="primary"
              size="lg"
              loading={loading}
              className="w-full justify-center mt-2 shadow-md shadow-teal-500/20"
              icon={ArrowRight}
              iconPosition="right"
            >
              Sign In to {selectedRole === 'admin' ? 'Admin Panel' : 'Doctor Panel'}
            </Button>
          </form>

          {/* 1-Click Fast Panel Login Buttons */}
          <div className="mt-6 pt-5 border-t border-slate-200/60">
            <p className="text-[10px] font-semibold text-slate-400 text-center uppercase tracking-wider mb-2.5">
              Instant 1-Click Panel Access
            </p>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => handleQuickLogin('doctor')}
                className="p-2.5 text-center rounded-xl bg-teal-50/80 hover:bg-teal-100/80 border border-teal-200/80 text-xs font-semibold text-teal-800 transition-colors flex items-center justify-center gap-1.5"
              >
                <Stethoscope className="w-3.5 h-3.5" />
                Doctor Panel
              </button>
              <button
                type="button"
                onClick={() => handleQuickLogin('admin')}
                className="p-2.5 text-center rounded-xl bg-purple-50/80 hover:bg-purple-100/80 border border-purple-200/80 text-xs font-semibold text-purple-800 transition-colors flex items-center justify-center gap-1.5"
              >
                <Shield className="w-3.5 h-3.5" />
                Admin Panel
              </button>
            </div>
          </div>
        </div>

        {/* Footer Security Badge */}
        <div className="mt-4 text-center">
          <p className="text-xs text-slate-500 flex items-center justify-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-teal-600" />
            Strict Panel Isolation • Zero Feature Leakage • SHA-256 Audit Trail
          </p>
        </div>
      </div>
    </GradientMesh>
  );
};

export default Login;
