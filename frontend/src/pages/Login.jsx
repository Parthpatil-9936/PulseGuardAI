import React, { useState } from 'react';
import { HeartPulse, Lock, Mail, Shield, Stethoscope, User, ArrowRight, Activity, CheckCircle2 } from 'lucide-react';
import { GradientMesh, Button, Input } from '../components/ui';
import { useAuth } from '../context/AuthContext';

export const Login = ({ onLoginSuccess }) => {
  const { login, DEMO_USERS } = useAuth();
  const [selectedRole, setSelectedRole] = useState('doctor');
  const [email, setEmail] = useState(DEMO_USERS.doctor.email);
  const [password, setPassword] = useState('••••••••••••');
  const [loading, setLoading] = useState(false);

  const handleRoleChange = (role) => {
    setSelectedRole(role);
    if (DEMO_USERS[role]) {
      setEmail(DEMO_USERS[role].email);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => {
      login(selectedRole, email);
      setLoading(false);
      onLoginSuccess?.();
    }, 450);
  };

  const handleQuickLogin = (role) => {
    setSelectedRole(role);
    setEmail(DEMO_USERS[role].email);
    login(role, DEMO_USERS[role].email);
    onLoginSuccess?.();
  };

  return (
    <GradientMesh className="flex items-center justify-center min-h-screen p-4">
      <div className="w-full max-w-md">
        {/* Glass Card Container */}
        <div className="glass-panel rounded-3xl p-8 sm:p-10 shadow-[0_20px_50px_rgba(0,0,0,0.08)] border border-white/60 relative overflow-hidden backdrop-blur-xl">
          {/* Subtle Glow Accent */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-48 h-1 bg-gradient-to-r from-transparent via-[#0EA5B7] to-transparent" />

          {/* Logo Mark */}
          <div className="flex flex-col items-center text-center mb-8">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-[#0D8A9A] to-[#0EA5B7] flex items-center justify-center text-white shadow-lg shadow-teal-500/25 mb-3.5 transition-transform hover:scale-105 duration-200">
              <HeartPulse className="w-8 h-8 animate-pulse" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">PulseGuard-AI</h1>
            <p className="text-xs text-slate-500 mt-1 max-w-xs">
              Deterministic Edge-Triage & Clinical Ward Gateway
            </p>
            <div className="mt-2 inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-teal-50 border border-teal-200/60 text-[11px] font-semibold text-teal-800">
              <span className="w-1.5 h-1.5 rounded-full bg-[#0EA5B7] animate-ping" />
              Edge Core Online :8000
            </div>
          </div>

          {/* Role Selector: Segmented Control */}
          <div className="mb-6">
            <label className="block text-xs font-semibold text-slate-700 mb-2">
              Select Clinician Role
            </label>
            <div className="grid grid-cols-3 gap-1.5 bg-slate-100/80 p-1.5 rounded-2xl border border-slate-200/60">
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
                Doctor
              </button>

              <button
                type="button"
                onClick={() => handleRoleChange('nurse')}
                className={`py-2 px-2 text-xs font-bold rounded-xl transition-all duration-200 flex flex-col items-center gap-1 ${
                  selectedRole === 'nurse'
                    ? 'bg-white text-[#2563EB] shadow-sm shadow-slate-200'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                <Activity className="w-4 h-4" />
                Nurse
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
                Admin
              </button>
            </div>
          </div>

          {/* Form */}
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
              label="Password / Clinical Passkey"
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
              Sign In to Ward Terminal
            </Button>
          </form>

          {/* Fast One-Click Demo Logins */}
          <div className="mt-8 pt-6 border-t border-slate-200/60">
            <p className="text-[11px] font-semibold text-slate-400 text-center uppercase tracking-wider mb-2.5">
              1-Click Demo Evaluation Profiles
            </p>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handleQuickLogin('doctor')}
                className="p-2 text-center rounded-xl bg-teal-50/80 hover:bg-teal-100/80 border border-teal-200/80 text-[11px] font-semibold text-teal-800 transition-colors"
              >
                Dr. Chen
              </button>
              <button
                type="button"
                onClick={() => handleQuickLogin('nurse')}
                className="p-2 text-center rounded-xl bg-blue-50/80 hover:bg-blue-100/80 border border-blue-200/80 text-[11px] font-semibold text-blue-800 transition-colors"
              >
                Nurse Priya
              </button>
              <button
                type="button"
                onClick={() => handleQuickLogin('admin')}
                className="p-2 text-center rounded-xl bg-purple-50/80 hover:bg-purple-100/80 border border-purple-200/80 text-[11px] font-semibold text-purple-800 transition-colors"
              >
                Admin Rivera
              </button>
            </div>
          </div>
        </div>

        {/* Footer Security Badge */}
        <div className="mt-4 text-center">
          <p className="text-xs text-slate-500 flex items-center justify-center gap-1.5">
            <Shield className="w-3.5 h-3.5 text-teal-600" />
            DPDP-Act Compliant • Tamper-Evident SHA-256 Ledger • Local Edge Safety Path
          </p>
        </div>
      </div>
    </GradientMesh>
  );
};

export default Login;
