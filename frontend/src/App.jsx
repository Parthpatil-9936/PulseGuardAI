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
import { DesignSystemPreview } from './pages/DesignSystemPreview';
import { Login } from './pages/Login';
import { CriticalAlertModal } from './components/patient/CriticalAlertModal';
import { useTelemetrySimulator } from './hooks/useTelemetrySimulator';
import { clinicalAudio } from './utils/audioAlarm';

function MainApp() {
  const { isAuthenticated, role } = useAuth();
  const { isAudioMuted } = useSystemHealth();

  // Navigation tab state
  const [currentTab, setCurrentTab] = useState(() => {
    // Check URL hash if available (e.g. #design-system)
    if (typeof window !== 'undefined' && window.location.hash === '#design-system') {
      return 'design-system';
    }
    return 'dashboard';
  });

  const [selectedBedId, setSelectedBedId] = useState('04');
  const [isTier1ModalForcedOpen, setIsTier1ModalForcedOpen] = useState(false);

  // Telemetry simulator hook
  const {
    beds,
    waveforms,
    activeTier1Bed,
    acknowledgeTier2Alert,
    acknowledgeTier1Alert,
    injectHypoxia,
    resetAllBeds,
  } = useTelemetrySimulator();

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
      if (window.location.hash === '#design-system') {
        setCurrentTab('design-system');
      } else if (window.location.hash === '#login') {
        setCurrentTab('login');
      }
    };
    window.addEventListener('hashchange', handleHash);
    return () => window.removeEventListener('hashchange', handleHash);
  }, []);

  // Not authenticated or explicitly on login tab? Show Login
  if (!isAuthenticated || currentTab === 'login') {
    return (
      <Login 
        onLoginSuccess={() => {
          window.location.hash = '';
          setCurrentTab('dashboard');
        }} 
      />
    );
  }

  // Design System Preview Mode (Phase 1 Deliverable)
  if (currentTab === 'design-system') {
    return (
      <DesignSystemPreview 
        onNavigateToApp={() => {
          window.location.hash = '';
          setCurrentTab('dashboard');
        }} 
      />
    );
  }

  // Handle opening patient detail
  const handleSelectBed = (bedId) => {
    setSelectedBedId(bedId);
    setCurrentTab('patient-detail');
  };

  return (
    <>
      <AppShell
        currentTab={currentTab}
        onSelectTab={setCurrentTab}
        onOpenDesignSystem={() => {
          window.location.hash = 'design-system';
          setCurrentTab('design-system');
        }}
      >
        {/* View Router */}
        {currentTab === 'dashboard' && (
          <WardDashboard
            beds={beds}
            waveforms={waveforms}
            onSelectBed={handleSelectBed}
            onInjectHypoxia={() => injectHypoxia('04')}
            onResetBeds={resetAllBeds}
          />
        )}

        {currentTab === 'patient-detail' && (
          <PatientDetail
            bed={activeBed}
            onBack={() => setCurrentTab('dashboard')}
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
