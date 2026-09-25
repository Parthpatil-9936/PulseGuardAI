import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

const API_BASE_URL = 'http://127.0.0.1:8000';

export const DEMO_PROFILES = {
  doctor: {
    id: 'usr_doc_01',
    name: 'Dr. Sarah Chen, MD',
    email: 'dr.chen@pulseguard.icu',
    defaultPassword: 'doctor123',
    role: 'doctor',
    title: 'Attending Cardiologist',
    department: 'Critical Care Unit 4',
    initials: 'SC',
    assignedBeds: ['01', '02', '04', '07', '10'],
    description: 'Directs patient care, reviews XAI diagnostics, prescribes interventions, requests transfers.'
  },
  nurse: {
    id: 'usr_nur_01',
    name: 'Priya Patel, RN',
    email: 'priya.rn@pulseguard.icu',
    defaultPassword: 'nurse123',
    role: 'nurse',
    title: 'Lead Critical Care Nurse',
    department: 'Ward 4 Floor Nursing',
    initials: 'PP',
    assignedBeds: ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10'],
    description: 'Manages bedside telemetry, acknowledges alarms, records clinical observations, mutes alarms.'
  },
  admin: {
    id: 'usr_adm_01',
    name: 'Alex Rivera',
    email: 'admin.rivera@pulseguard.icu',
    defaultPassword: 'admin123',
    role: 'admin',
    title: 'Hospital Clinical Systems Admin',
    department: 'Biomedical Informatics',
    initials: 'AR',
    assignedBeds: [],
    description: 'Administers RBAC staff, approves/rejects transfers, verifies SHA-256 ledger, issues break-glass tokens.'
  }
};

// Strict Panel Isolation Matrix: which tabs are permitted for each role
export const PANEL_PERMISSIONS = {
  doctor: ['dashboard', 'patient-detail', 'patients', 'transfers', 'notes', 'design-system'],
  nurse: ['dashboard', 'patient-detail', 'patients', 'notes', 'design-system'],
  admin: ['analytics', 'transfers', 'users', 'audit', 'emergency', 'dashboard', 'patient-detail', 'patients', 'design-system']
};

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(() => localStorage.getItem('pulseguard_token') || null);
  const [role, setRole] = useState(() => localStorage.getItem('pulseguard_role') || null);
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('pulseguard_user');
    if (saved) {
      try { return JSON.parse(saved); } catch (e) {}
    }
    return null;
  });

  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    return Boolean(localStorage.getItem('pulseguard_token') && localStorage.getItem('pulseguard_role'));
  });

  // Verify whether a given tab is authorized for current role
  const canAccessTab = (tab) => {
    if (!role) return false;
    const allowed = PANEL_PERMISSIONS[role.toLowerCase()] || [];
    return allowed.includes(tab);
  };

  // Login handler: contacts FastAPI backend /auth/login with graceful offline fallback
  const login = async (email, password, roleHint = 'doctor') => {
    const cleanEmail = email.trim().toLowerCase();
    let authToken = null;
    let authUser = null;
    let authRole = roleHint.toLowerCase();

    // Find profile matching email or hint
    const matchedProfile = Object.values(DEMO_PROFILES).find(p => p.email === cleanEmail) || DEMO_PROFILES[authRole];
    if (matchedProfile) {
      authRole = matchedProfile.role;
    }

    try {
      // Attempt backend FastAPI authentication
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: cleanEmail, password })
      });

      if (response.ok) {
        const data = await response.json();
        authToken = data.access_token;
        authRole = data.role.toLowerCase();
        authUser = {
          id: data.user_id,
          name: data.name,
          email: cleanEmail,
          role: authRole,
          department: matchedProfile?.department || 'Critical Care',
          assignedBeds: matchedProfile?.assignedBeds || []
        };
      }
    } catch (err) {
      console.warn('Backend API unreachable, using local authenticated clinical profile:', err);
    }

    // Fallback if backend is currently launching or standalone
    if (!authToken) {
      authToken = `local_jwt_${Date.now()}_${authRole}`;
      authUser = matchedProfile || DEMO_PROFILES[authRole];
    }

    setToken(authToken);
    setRole(authRole);
    setUser(authUser);
    setIsAuthenticated(true);

    localStorage.setItem('pulseguard_token', authToken);
    localStorage.setItem('pulseguard_role', authRole);
    localStorage.setItem('pulseguard_user', JSON.stringify(authUser));
    localStorage.setItem('pulseguard_auth', 'true');

    return authRole;
  };

  const logout = () => {
    setToken(null);
    setRole(null);
    setUser(null);
    setIsAuthenticated(false);

    localStorage.removeItem('pulseguard_token');
    localStorage.removeItem('pulseguard_role');
    localStorage.removeItem('pulseguard_user');
    localStorage.removeItem('pulseguard_auth');
  };

  return (
    <AuthContext.Provider value={{
      token,
      user,
      role,
      isAuthenticated,
      login,
      logout,
      canAccessTab,
      DEMO_PROFILES,
      PANEL_PERMISSIONS
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
