import React, { useState } from 'react';
import { 
  HeartPulse, 
  Lock, 
  Mail, 
  User,
  Shield, 
  Stethoscope, 
  ArrowRight, 
  ShieldCheck, 
  AlertCircle 
} from 'lucide-react';
import { GradientMesh, Button, Input, Select } from '../components/ui';
import { useAuth } from '../context/AuthContext';

export const Login = ({ onLoginSuccess }) => {
  const { login, register, loginWithGoogle } = useAuth();
  
  const [isRegister, setIsRegister] = useState(false);
  const [selectedRole, setSelectedRole] = useState('doctor');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);

    try {
      if (isRegister) {
        await register(name, email, password, selectedRole);
      } else {
        await login(email, password);
      }
      setLoading(false);
      onLoginSuccess?.();
    } catch (err) {
      setLoading(false);
      setErrorMsg(isRegister ? 'Registration failed. Email might be taken.' : 'Authentication failed. Please verify credentials.');
    }
  };

  const handleGoogleAuth = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      // In a real app, this would trigger OAuth popup. Here we prompt for email to simulate.
      const mockEmail = prompt("Google Auth Simulation:\nEnter your Google Email (e.g., dr.smith@gmail.com):");
      if (!mockEmail) {
        setLoading(false);
        return;
      }
      const mockName = prompt("Enter your Name:", "Google User");
      await loginWithGoogle(mockEmail, mockName || "Google User");
      setLoading(false);
      onLoginSuccess?.();
    } catch (err) {
      setLoading(false);
      setErrorMsg('Google authentication failed.');
    }
  };

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

          {/* Mode Selector: Login vs Register */}
          <div className="mb-6">
            <div className="grid grid-cols-2 gap-2 bg-slate-100/90 p-1.5 rounded-2xl border border-slate-200/60">
              <button
                type="button"
                onClick={() => { setIsRegister(false); setErrorMsg(null); }}
                className={`py-2 px-2 text-sm font-bold rounded-xl transition-all duration-200 flex flex-col items-center gap-1 ${
                  !isRegister
                    ? 'bg-white text-[#0D8A9A] shadow-sm shadow-slate-200'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={() => { setIsRegister(true); setErrorMsg(null); }}
                className={`py-2 px-2 text-sm font-bold rounded-xl transition-all duration-200 flex flex-col items-center gap-1 ${
                  isRegister
                    ? 'bg-white text-[#0D8A9A] shadow-sm shadow-slate-200'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                Register
              </button>
            </div>
          </div>

          {/* Role Selector: Only show when Registering */}
          {isRegister && (
            <div className="mb-5">
              <label className="block text-xs font-semibold text-slate-700 mb-2">
                Select Role to Register As
              </label>
              <div className="grid grid-cols-2 gap-2 bg-slate-50 p-1 rounded-xl border border-slate-200">
                <button
                  type="button"
                  onClick={() => setSelectedRole('doctor')}
                  className={`py-1.5 px-2 text-xs font-bold rounded-lg transition-all duration-200 flex items-center justify-center gap-1.5 ${
                    selectedRole === 'doctor'
                      ? 'bg-[#0D8A9A] text-white shadow-sm'
                      : 'text-slate-500 hover:bg-slate-200'
                  }`}
                >
                  <Stethoscope className="w-3.5 h-3.5" />
                  Doctor
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedRole('admin')}
                  className={`py-1.5 px-2 text-xs font-bold rounded-lg transition-all duration-200 flex items-center justify-center gap-1.5 ${
                    selectedRole === 'admin'
                      ? 'bg-purple-600 text-white shadow-sm'
                      : 'text-slate-500 hover:bg-slate-200'
                  }`}
                >
                  <Shield className="w-3.5 h-3.5" />
                  Admin
                </button>
              </div>
            </div>
          )}

          {errorMsg && (
            <div className="mb-4 p-3 rounded-xl bg-red-50 border border-red-200 text-xs text-red-700 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {isRegister && (
              <Input
                label="Full Name"
                type="text"
                icon={User}
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            )}

            <Input
              label="Staff Email"
              type="email"
              icon={Mail}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />

            <Input
              label="Password"
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
              {isRegister ? 'Register Account' : 'Sign In'}
            </Button>
          </form>

          {/* Google Auth & Toggle */}
          <div className="mt-6 pt-5 border-t border-slate-200/60 flex flex-col gap-3">
            <button
              type="button"
              onClick={handleGoogleAuth}
              className="w-full py-2.5 px-4 bg-white border border-slate-300 rounded-xl text-sm font-semibold text-slate-700 hover:bg-slate-50 transition-colors flex items-center justify-center gap-2 shadow-sm"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
              </svg>
              {isRegister ? 'Sign up with Google' : 'Sign in with Google'}
            </button>

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
