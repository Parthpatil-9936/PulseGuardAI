import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { SystemHealthProvider, useSystemHealth } from './context/SystemHealthContext';
import { TransferProvider } from './context/TransferContext';
import { AppShell } from './components/layout/AppShell';
import { WardDashboard } from './pages/WardDashboard';
import { PatientDetail } from './pages/PatientDetail';
import { PatientRoster } from './pages/PatientRoster';
import { TransferQueue } from './pages/TransferQueue';
import { ClinicalNotesPage } from './pages/ClinicalNotesPage';
import { UserManagement } from './pages/admin/UserManagement';
import { AuditLogViewer } from './pages/admin/AuditLogViewer';
import { EmergencyAccess } from './pages/admin/EmergencyAccess';
import { AnalyticsDashboard } from './pages/admin/AnalyticsDashboard';
import { Login } from './pages/Login';
import { CriticalAlertModal } from './components/patient/CriticalAlertModal';
import { AccessDenied } from './components/common/AccessDenied';
import { useTelemetrySimulator } from './hooks/useTelemetrySimulator';
import { clinicalAudio } from './utils/audioAlarm';

function MainApp() {
  const { isAuthenticated, role, canAccessTab } = useAuth();
  const { isAudioMuted } = useSystemHealth();

  // Navigation tab state
  const [currentTab, setCurrentTab] = useState(() => {
    const savedRole = typeof window !== 'undefined' ? localStorage.getItem('pulseguard_role') : null;
    return savedRole === 'admin' ? 'analytics' : 'dashboard';
  });

  const [selectedBedId, setSelectedBedId] = useState(null);
  const [isTier1ModalForcedOpen, setIsTier1ModalForcedOpen] = useState(false);

  // Telemetry simulator hook
  const {
    beds,
    waveforms,
    activeTier1Bed,
    loading: bedsLoading,
    acknowledgeTier2Alert,
    acknowledgeTier1Alert,
    refreshBeds,
  } = useTelemetrySimulator();

  // Select first bed by default once beds load
  useEffect(() => {
    if (!selectedBedId && beds.length > 0) {
      setSelectedBedId(beds[0].bedId);
    }
  }, [beds, selectedBedId]);

  // Find currently selected bed object
  const activeBed = beds.find(b => b.bedId === selectedBedId) || beds[0];

  // Audio alert trigger when unacknowledged Tier 1 alert exists
  useEffect(() => {
    if (activeTier1Bed && !isAudioMuted) {
      const interval = setInterval(() => {
        clinicalAudio.playTier1Beep();
      }, 2500);
      return () => clearInterval(interval);
    }
  }, [activeTier1Bed, isAudioMuted]);

  // Handle URL hash changes
  useEffect(() => {
    const handleHash = () => {
      if (window.location.hash === '#login') {
        setCurrentTab('login');
      }
    };
    window.addEventListener('hashchange', handleHash);
    return () => window.removeEventListener('hashchange', handleHash);
  }, []);

  // Automatically synchronize tab if currentTab is forbidden for the active role
  useEffect(() => {
    if (isAuthenticated && role) {
      if (currentTab !== 'login' && !canAccessTab(currentTab)) {
        setCurrentTab(role === 'admin' ? 'analytics' : 'dashboard');
      }
    }
  }, [role, isAuthenticated]);

  const getRequiredRole = (tab) => {
    if (tab === 'transfers') return 'Doctor or Administrator';
    if (tab === 'notes') return 'Doctor or Administrator (Clinical Care)';
    if (['users', 'audit', 'emergency', 'analytics'].includes(tab)) return 'Administrator';
    return 'Authorized Staff';
  };

  // Not authenticated or explicitly on login tab? Show Login
  if (!isAuthenticated || currentTab === 'login') {
    return (
      <Login 
        onLoginSuccess={() => {
          window.location.hash = '';
          const savedRole = localStorage.getItem('pulseguard_role') || role;
          setCurrentTab(savedRole === 'admin' ? 'analytics' : 'dashboard');
        }} 
      />
    );
  }


  // Handle opening patient detail
  const handleSelectBed = (bedId) => {
    setSelectedBedId(bedId);
    setCurrentTab('patient-detail');
  };

  const isCurrentTabAuthorized = canAccessTab(currentTab);

  return (
    <>
      <AppShell
        currentTab={currentTab}
        onSelectTab={setCurrentTab}
      >
        {/* Strict Panel Isolation Barrier: if tab is forbidden, render AccessDenied */}
        {!isCurrentTabAuthorized ? (
          <AccessDenied
            attemptedTab={currentTab}
            requiredRole={getRequiredRole(currentTab)}
            onGoHome={() => setCurrentTab(role === 'admin' ? 'analytics' : 'dashboard')}
          />
        ) : (
          <>
            {/* View Router for Authorized Features */}
            {currentTab === 'dashboard' && (
              <WardDashboard
                beds={beds}
                waveforms={waveforms}
                onSelectBed={handleSelectBed}
              />
            )}

            {currentTab === 'patient-detail' && (
              <PatientDetail
                bed={activeBed}
                onBack={() => setCurrentTab(role === 'admin' ? 'analytics' : 'dashboard')}
                onAcknowledgeTier2={acknowledgeTier2Alert}
                onTriggerTier1Modal={(bed) => {
                  setSelectedBedId(bed.bedId);
                  setIsTier1ModalForcedOpen(true);
                }}
              />
            )}

            {currentTab === 'patients' && (
              <PatientRoster
                beds={beds}
                onSelectBed={handleSelectBed}
              />
            )}

            {currentTab === 'transfers' && (
              <TransferQueue />
            )}

            {currentTab === 'notes' && (
              <ClinicalNotesPage beds={beds} />
            )}

            {currentTab === 'users' && (
              <UserManagement />
            )}

            {currentTab === 'audit' && (
              <AuditLogViewer />
            )}

            {currentTab === 'emergency' && (
              <EmergencyAccess />
            )}

            {currentTab === 'analytics' && (
              <AnalyticsDashboard />
            )}
          </>
        )}
      </AppShell>

      {/* Phase 4 Tier 1 Critical Alarm Takeover Modal */}
      <CriticalAlertModal
        isOpen={Boolean(activeTier1Bed) || isTier1ModalForcedOpen}
        bed={activeTier1Bed || activeBed}
        onAcknowledge={(bedId, clinicianName) => {
          acknowledgeTier1Alert(bedId, clinicianName);
          setIsTier1ModalForcedOpen(false);
        }}
      />
    </>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <SystemHealthProvider>
        <TransferProvider>
          <MainApp />
        </TransferProvider>
      </SystemHealthProvider>
    </AuthProvider>
  );
}
