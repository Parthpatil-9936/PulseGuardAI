import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

const DEMO_USERS = {
  doctor: {
    id: 'usr_doc_01',
    name: 'Dr. Sarah Chen, MD',
    email: 'dr.chen@pulseguard.icu',
    role: 'doctor',
    title: 'Attending Cardiologist',
    department: 'Critical Care Unit 4',
    initials: 'SC',
    assignedBeds: ['01', '02', '04', '07', '10'],
  },
  nurse: {
    id: 'usr_nur_01',
    name: 'Priya Patel, RN',
    email: 'priya.rn@pulseguard.icu',
    role: 'nurse',
    title: 'Lead Critical Care Nurse',
    department: 'Ward 4 Floor',
    initials: 'PP',
    assignedBeds: ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10'],
  },
  admin: {
    id: 'usr_adm_01',
    name: 'Alex Rivera',
    email: 'admin.rivera@pulseguard.icu',
    role: 'admin',
    title: 'Hospital Clinical Systems Admin',
    department: 'Biomedical Informatics',
    initials: 'AR',
    assignedBeds: [],
  }
};

export const AuthProvider = ({ children }) => {
  const [role, setRole] = useState(() => {
    return localStorage.getItem('pulseguard_role') || 'doctor';
  });

  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    const stored = localStorage.getItem('pulseguard_auth');
    if (stored === null) return true;
    return stored === 'true';
  });

  const [user, setUser] = useState(() => {
    const initialRole = localStorage.getItem('pulseguard_role') || 'doctor';
    return DEMO_USERS[initialRole] || DEMO_USERS.doctor;
  });

  const switchRole = (newRole) => {
    if (DEMO_USERS[newRole]) {
      setRole(newRole);
      setUser(DEMO_USERS[newRole]);
      localStorage.setItem('pulseguard_role', newRole);
    }
  };

  const login = (selectedRole = 'doctor', email = '') => {
    const chosenRole = selectedRole.toLowerCase();
    const newUser = DEMO_USERS[chosenRole] || DEMO_USERS.doctor;
    setRole(chosenRole);
    setUser(newUser);
    setIsAuthenticated(true);
    localStorage.setItem('pulseguard_role', chosenRole);
    localStorage.setItem('pulseguard_auth', 'true');
  };

  const logout = () => {
    setIsAuthenticated(false);
    localStorage.setItem('pulseguard_auth', 'false');
  };

  return (
    <AuthContext.Provider value={{
      user,
      role,
      isAuthenticated,
      login,
      logout,
      switchRole,
      DEMO_USERS
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
