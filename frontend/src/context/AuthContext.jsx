import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

const API_BASE_URL = 'http://127.0.0.1:8000';



// Strict Panel Isolation Matrix: which tabs are permitted for each role
export const PANEL_PERMISSIONS = {
  doctor: ['dashboard', 'patient-detail', 'patients', 'transfers', 'notes', 'design-system'],
  admin: ['analytics', 'transfers', 'users', 'audit', 'emergency', 'dashboard', 'patient-detail', 'patients', 'notes', 'design-system']
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

  useEffect(() => {
    const validateToken = async () => {
      const storedToken = localStorage.getItem('pulseguard_token');
      if (storedToken) {
        try {
          const res = await fetch(`${API_BASE_URL}/auth/me`, {
            headers: { 'Authorization': `Bearer ${storedToken}` }
          });
          if (!res.ok) {
            logout();
          }
        } catch (err) {
          logout();
        }
      }
    };
    validateToken();
  }, []);

  // Verify whether a given tab is authorized for current role
  const canAccessTab = (tab) => {
    if (!role) return false;
    const allowed = PANEL_PERMISSIONS[role.toLowerCase()] || [];
    return allowed.includes(tab);
  };

  const login = async (email, password) => {
    const cleanEmail = email.trim().toLowerCase();
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: cleanEmail, password })
    });

    if (!response.ok) {
      throw new Error("Authentication failed");
    }

    const data = await response.json();
    const authRole = data.role.toLowerCase();
    const authUser = {
      id: data.user_id,
      name: data.name,
      email: cleanEmail,
      role: authRole,
      department: 'Critical Care',
      assignedBeds: []
    };

    setToken(data.access_token);
    setRole(authRole);
    setUser(authUser);
    setIsAuthenticated(true);

    localStorage.setItem('pulseguard_token', data.access_token);
    localStorage.setItem('pulseguard_role', authRole);
    localStorage.setItem('pulseguard_user', JSON.stringify(authUser));
    localStorage.setItem('pulseguard_auth', 'true');

    return authRole;
  };

  const register = async (name, email, password, role) => {
    const cleanEmail = email.trim().toLowerCase();
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email: cleanEmail, password, role })
    });

    if (!response.ok) {
      throw new Error("Registration failed");
    }

    const data = await response.json();
    const authRole = data.role.toLowerCase();
    const authUser = {
      id: data.user_id,
      name: data.name,
      email: cleanEmail,
      role: authRole,
      department: 'Critical Care',
      assignedBeds: []
    };

    setToken(data.access_token);
    setRole(authRole);
    setUser(authUser);
    setIsAuthenticated(true);

    localStorage.setItem('pulseguard_token', data.access_token);
    localStorage.setItem('pulseguard_role', authRole);
    localStorage.setItem('pulseguard_user', JSON.stringify(authUser));
    localStorage.setItem('pulseguard_auth', 'true');

    return authRole;
  };

  const loginWithGoogle = async (email, name) => {
    const cleanEmail = email.trim().toLowerCase();
    const response = await fetch(`${API_BASE_URL}/auth/google`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: cleanEmail, name })
    });

    if (!response.ok) {
      throw new Error("Google authentication failed");
    }

    const data = await response.json();
    const authRole = data.role.toLowerCase();
    const authUser = {
      id: data.user_id,
      name: data.name,
      email: cleanEmail,
      role: authRole,
      department: 'Critical Care',
      assignedBeds: []
    };

    setToken(data.access_token);
    setRole(authRole);
    setUser(authUser);
    setIsAuthenticated(true);

    localStorage.setItem('pulseguard_token', data.access_token);
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
      PANEL_PERMISSIONS,
      register,
      loginWithGoogle
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
