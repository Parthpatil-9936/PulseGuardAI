import React from 'react';
import { ShieldAlert, Lock, ArrowLeft, Home } from 'lucide-react';
import { Button, Badge } from '../ui';
import { useAuth } from '../../context/AuthContext';

export const AccessDenied = ({ requiredRole, attemptedTab, onGoHome }) => {
  const { user, role } = useAuth();

  return (
    <div className="min-h-[70vh] flex items-center justify-center p-6">
      <div className="max-w-md w-full bg-white rounded-3xl p-8 border border-red-200/80 shadow-xl text-center space-y-5">
        <div className="w-16 h-16 rounded-2xl bg-red-50 border border-red-200 flex items-center justify-center mx-auto text-red-600 shadow-sm animate-bounce">
          <ShieldAlert className="w-9 h-9" />
        </div>

        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-red-100 text-red-800 text-xs font-bold mb-2">
            <Lock className="w-3.5 h-3.5" />
            403 Forbidden — Panel Isolated
          </div>
          <h2 className="text-xl font-extrabold text-slate-900 tracking-tight">
            Access Restricted to {requiredRole.toUpperCase()}
          </h2>
          <p className="text-xs text-slate-500 mt-2 leading-relaxed">
            Your current clinical session is authenticated as <strong>{user?.name || 'Staff'}</strong> with role{' '}
            <Badge variant={role} size="sm">{role.toUpperCase()}</Badge>. Under hospital RBAC governance, the 
            features of this panel are strictly isolated and not accessible from your role.
          </p>
        </div>

        <div className="p-3.5 bg-slate-50 rounded-2xl border border-slate-100 text-left text-xs space-y-1.5 font-mono">
          <div className="flex justify-between text-slate-500">
            <span>Attempted Resource:</span>
            <span className="font-bold text-slate-800">/{attemptedTab}</span>
          </div>
          <div className="flex justify-between text-slate-500">
            <span>Required Clearance:</span>
            <span className="font-bold text-red-600">{requiredRole.toUpperCase()}</span>
          </div>
          <div className="flex justify-between text-slate-500">
            <span>Audit Action:</span>
            <span className="text-teal-700">AUTHZ_DENIAL_RECORDED</span>
          </div>
        </div>

        <div className="pt-2 flex justify-center">
          <Button
            variant="primary"
            size="md"
            icon={Home}
            onClick={onGoHome}
            className="w-full justify-center"
          >
            Return to Authorized Dashboard
          </Button>
        </div>
      </div>
    </div>
  );
};

export default AccessDenied;
