import React, { useState } from 'react';
import { 
  HeartPulse, 
  LayoutDashboard, 
  Users, 
  ArrowLeftRight, 
  FileText, 
  ShieldCheck, 
  KeyRound, 
  BarChart3, 
  Layers, 
  LogOut, 
  Wifi, 
  WifiOff, 
  Volume2, 
  VolumeX, 
  Bell, 
  ChevronLeft, 
  ChevronRight,
  Activity,
  CheckCircle2,
  AlertTriangle,
  Server,
  Database,
  Cpu,
  RefreshCw,
  Sparkles
} from 'lucide-react';
import { Badge, Avatar, Button, Tooltip } from '../ui';
import { useAuth } from '../../context/AuthContext';
import { useSystemHealth } from '../../context/SystemHealthContext';

export const AppShell = ({
  currentTab,
  onSelectTab,
  children,
  onOpenDesignSystem,
}) => {
  const { user, role, switchRole, logout } = useAuth();
  const { 
    isCloudOutage, 
    toggleCloudOutage, 
    isAudioMuted, 
    muteRemainingSeconds, 
    toggleMute, 
    services,
    latencyMs 
  } = useSystemHealth();

  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);

  // Role-aware navigation definitions
  const navItems = [
    {
      id: 'dashboard',
      label: 'Ward Dashboard',
      icon: LayoutDashboard,
      roles: ['admin', 'doctor', 'nurse'],
      badge: '10 Beds',
    },
    {
      id: 'patients',
      label: 'Patient Roster',
      icon: Users,
      roles: ['admin', 'doctor', 'nurse'],
    },
    {
      id: 'transfers',
      label: role === 'admin' ? 'Transfer Queue' : 'Transfer Requests',
      icon: ArrowLeftRight,
      roles: ['admin', 'doctor'],
      badge: role === 'admin' ? '1 Pending' : null,
      badgeVariant: 'tier2',
    },
    {
      id: 'notes',
      label: 'Clinical Notes',
      icon: FileText,
      roles: ['doctor', 'nurse'],
    },
    {
      id: 'users',
      label: 'Staff Management',
      icon: ShieldCheck,
      roles: ['admin'],
    },
    {
      id: 'audit',
      label: 'Audit Ledger (SHA-256)',
      icon: KeyRound,
      roles: ['admin'],
      badge: 'Verified',
      badgeVariant: 'normal',
    },
    {
      id: 'emergency',
      label: 'Emergency Access',
      icon: Sparkles,
      roles: ['admin'],
    },
    {
      id: 'analytics',
      label: 'Ward Analytics',
      icon: BarChart3,
      roles: ['admin'],
    },
  ];

  const visibleNav = navItems.filter(item => item.roles.includes(role));

  return (
    <div className="flex h-screen bg-[#F8FAFC] text-slate-900 overflow-hidden">
      {/* 1. Left Persistent Sidebar */}
      <aside 
        className={`bg-white border-r border-slate-200/80 flex flex-col justify-between transition-all duration-300 z-30 shrink-0 select-none ${
          sidebarCollapsed ? 'w-20' : 'w-64'
        }`}
      >
        {/* Brand / Logo */}
        <div>
          <div className="h-16 px-4 flex items-center justify-between border-b border-slate-100">
            <div className="flex items-center gap-3 overflow-hidden">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-[#0D8A9A] to-[#0EA5B7] flex items-center justify-center text-white shadow-md shadow-teal-500/20 shrink-0">
                <HeartPulse className="w-6 h-6 animate-pulse" />
              </div>
              {!sidebarCollapsed && (
                <div className="leading-tight truncate">
                  <span className="font-extrabold text-slate-900 tracking-tight text-base block">
                    PulseGuard<span className="text-[#0EA5B7]">-AI</span>
                  </span>
                  <span className="text-[10px] text-slate-400 font-medium tracking-wide uppercase">
                    Edge Triage v3.0
                  </span>
                </div>
              )}
            </div>

            <button
              type="button"
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
              title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              {sidebarCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
            </button>
          </div>

          {/* Navigation Links */}
          <nav className="p-3 space-y-1 overflow-y-auto max-h-[calc(100vh-230px)]">
            {visibleNav.map((item) => {
              const Icon = item.icon;
              const isActive = currentTab === item.id;

              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => onSelectTab(item.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl font-medium text-xs transition-all duration-150 group relative ${
                    isActive
                      ? 'bg-teal-50 text-[#0D8A9A] font-semibold shadow-sm'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`}
                >
                  <Icon className={`w-4 h-4 shrink-0 transition-transform group-hover:scale-110 ${
                    isActive ? 'text-[#0EA5B7]' : 'text-slate-400 group-hover:text-slate-700'
                  }`} />

                  {!sidebarCollapsed && (
                    <span className="truncate flex-1 text-left">{item.label}</span>
                  )}

                  {!sidebarCollapsed && item.badge && (
                    <Badge variant={item.badgeVariant || 'normal'} size="sm">
                      {item.badge}
                    </Badge>
                  )}

                  {sidebarCollapsed && (
                    <div className="absolute left-full ml-2 px-2.5 py-1 bg-slate-900 text-white text-xs rounded-md whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-50 shadow-md">
                      {item.label}
                    </div>
                  )}
                </button>
              );
            })}

            {/* Design System Preview Quick Link */}
            <div className="pt-2 mt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={onOpenDesignSystem}
                className="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium text-slate-500 hover:text-slate-900 hover:bg-slate-50 transition-colors group relative"
              >
                <Layers className="w-4 h-4 text-slate-400 group-hover:text-[#0EA5B7] shrink-0" />
                {!sidebarCollapsed && <span>Design System Preview</span>}
                {sidebarCollapsed && (
                  <div className="absolute left-full ml-2 px-2 py-1 bg-slate-900 text-white text-xs rounded whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none z-50">
                    Design System
                  </div>
                )}
              </button>
            </div>
          </nav>
        </div>

        {/* Clinician Profile Footer */}
        <div className="p-3 border-t border-slate-100 bg-slate-50/50">
          <div className="flex items-center gap-3">
            <Avatar 
              name={user.name} 
              role={user.role} 
              size={sidebarCollapsed ? 'sm' : 'md'} 
              status="online" 
            />
            {!sidebarCollapsed && (
              <div className="flex-1 min-w-0">
                <p className="text-xs font-bold text-slate-900 truncate leading-tight">
                  {user.name}
                </p>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <Badge variant={user.role} size="sm">
                    {user.role.toUpperCase()}
                  </Badge>
                </div>
              </div>
            )}
            {!sidebarCollapsed && (
              <button
                type="button"
                onClick={logout}
                className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                title="Log Out"
              >
                <LogOut className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </aside>

      {/* 2. Main Content Canvas */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Bar */}
        <header className="h-16 px-6 glass-panel border-b border-slate-200/80 flex items-center justify-between z-20 shrink-0">
          {/* Left: Active View title + Role pill */}
          <div className="flex items-center gap-3">
            <h2 className="text-base font-bold text-slate-900 tracking-tight capitalize">
              {currentTab.replace('-', ' ')}
            </h2>
            <span className="text-slate-300">/</span>
            <span className="text-xs text-slate-500 font-medium">Critical Care Unit 4</span>

            {/* Quick Role Switcher for Hackathon Testing */}
            <div className="hidden sm:flex items-center bg-slate-100 p-0.5 rounded-xl border border-slate-200 ml-2">
              <button
                type="button"
                onClick={() => switchRole('doctor')}
                className={`text-[11px] font-bold px-2.5 py-1 rounded-lg transition-all ${
                  role === 'doctor' ? 'bg-white text-[#0D8A9A] shadow-xs' : 'text-slate-500 hover:text-slate-900'
                }`}
              >
                Doctor
              </button>
              <button
                type="button"
                onClick={() => switchRole('nurse')}
                className={`text-[11px] font-bold px-2.5 py-1 rounded-lg transition-all ${
                  role === 'nurse' ? 'bg-white text-[#2563EB] shadow-xs' : 'text-slate-500 hover:text-slate-900'
                }`}
              >
                Nurse
              </button>
              <button
                type="button"
                onClick={() => switchRole('admin')}
                className={`text-[11px] font-bold px-2.5 py-1 rounded-lg transition-all ${
                  role === 'admin' ? 'bg-white text-purple-700 shadow-xs' : 'text-slate-500 hover:text-slate-900'
                }`}
              >
                Admin
              </button>
            </div>
          </div>

          {/* Right Actions: Outage Toggle, Mute Clamping, Notifications, User */}
          <div className="flex items-center gap-3">
            {/* Cloud Outage Simulator Toggle (Admin and Doctor only) */}
            {(role === 'admin' || role === 'doctor') && (
              <Tooltip 
                content={isCloudOutage ? "Restore Hospital WAN Sync" : "Simulate complete external cloud outage (test edge resilience)"}
                position="bottom"
              >
                <button
                  type="button"
                  onClick={toggleCloudOutage}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all duration-200 ${
                    isCloudOutage
                      ? 'bg-amber-500 text-white border-amber-600 shadow-sm shadow-amber-500/20'
                      : 'bg-white text-slate-700 hover:bg-slate-50 border-slate-200 shadow-sm'
                  }`}
                >
                  {isCloudOutage ? (
                    <>
                      <WifiOff className="w-3.5 h-3.5 animate-pulse" />
                      <span>Cloud Outage Active</span>
                    </>
                  ) : (
                    <>
                      <Wifi className="w-3.5 h-3.5 text-teal-600" />
                      <span>Simulate Cloud Outage</span>
                    </>
                  )}
                </button>
              </Tooltip>
            )}

            {/* Siren Mute with 300s clamp */}
            <Tooltip 
              content={isAudioMuted ? `Muted: Auto-unmutes in ${muteRemainingSeconds}s (max 300s anti-tamper clamp)` : 'Silence telemetry alarms (capped to 5 minutes)'}
              position="bottom"
            >
              <button
                type="button"
                onClick={toggleMute}
                className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl text-xs font-medium border transition-colors ${
                  isAudioMuted
                    ? 'bg-rose-50 text-rose-700 border-rose-200'
                    : 'bg-white text-slate-600 hover:bg-slate-50 border-slate-200'
                }`}
              >
                {isAudioMuted ? (
                  <>
                    <VolumeX className="w-4 h-4 text-rose-600" />
                    <span className="font-mono font-bold text-[11px]">{muteRemainingSeconds}s</span>
                  </>
                ) : (
                  <>
                    <Volume2 className="w-4 h-4 text-slate-500" />
                    <span className="hidden md:inline text-[11px]">Audio On</span>
                  </>
                )}
              </button>
            </Tooltip>

            {/* Notification Bell */}
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowNotifications(!showNotifications)}
                className="p-2 rounded-xl text-slate-500 hover:text-slate-800 hover:bg-slate-100/80 transition-colors relative"
                aria-label="Notifications"
              >
                <Bell className="w-4 h-4" />
                <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-red-500 ring-2 ring-white animate-pulse" />
              </button>

              {/* Notification Popup Dropdown */}
              {showNotifications && (
                <div className="absolute right-0 mt-2 w-80 rounded-2xl bg-white shadow-2xl border border-slate-200 p-4 z-50 text-xs">
                  <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-100">
                    <span className="font-bold text-slate-900">Live Ward Alerts (2)</span>
                    <span className="text-[10px] text-teal-600 font-semibold cursor-pointer" onClick={() => setShowNotifications(false)}>Close</span>
                  </div>
                  <div className="space-y-2">
                    <div className="p-2.5 rounded-xl bg-red-50 border border-red-200">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-bold text-red-900">Bed 04 • Julian Drake</span>
                        <span className="text-[10px] text-red-600 font-mono">Just now</span>
                      </div>
                      <p className="text-red-700 text-[11px]">Tier 1 Critical: Acute desaturation (SpO2 81%). Unsuppressable siren active.</p>
                    </div>

                    <div className="p-2.5 rounded-xl bg-amber-50 border border-amber-200">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-bold text-amber-900">Bed 02 • Marcus Sterling</span>
                        <span className="text-[10px] text-amber-600 font-mono">2m ago</span>
                      </div>
                      <p className="text-amber-700 text-[11px]">Tier 2 Warning: SpO2 downward trend (92%). Acknowledgment pending.</p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Clinician Pill */}
            <div className="flex items-center gap-2 pl-2 border-l border-slate-200">
              <Avatar name={user.name} role={user.role} size="sm" />
              <div className="hidden xl:block text-left">
                <span className="text-xs font-bold text-slate-900 block leading-tight">{user.name}</span>
                <span className="text-[10px] text-slate-400 capitalize">{user.role}</span>
              </div>
            </div>
          </div>
        </header>

        {/* 3. System Health Strip (slim bar directly beneath top bar) */}
        <div className="px-6 py-1.5 bg-slate-900 text-slate-300 text-[11px] font-mono flex items-center justify-between z-10 shrink-0 border-b border-slate-800">
          {/* Status Dots */}
          <div className="flex items-center gap-4 flex-wrap">
            <span className="text-slate-400 font-bold uppercase tracking-wider text-[10px] mr-1">
              Engine Health:
            </span>

            {/* FastAPI */}
            <Tooltip content="FastAPI Edge Gateway running on port 8000" position="bottom">
              <div className="flex items-center gap-1.5 cursor-help">
                <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400/50" />
                <span className="text-slate-200">FastAPI</span>
                <span className="text-slate-400 text-[10px]">:8000</span>
              </div>
            </Tooltip>

            {/* Redis */}
            <Tooltip content="Redis volatile 10s FIFO telemetry buffer" position="bottom">
              <div className="flex items-center gap-1.5 cursor-help">
                <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400/50" />
                <span className="text-slate-200">Redis</span>
                <span className="text-slate-400 text-[10px]">Buffer</span>
              </div>
            </Tooltip>

            {/* PostgreSQL */}
            <Tooltip content="PostgreSQL continuous SHA-256 cryptographic audit chain" position="bottom">
              <div className="flex items-center gap-1.5 cursor-help">
                <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400/50" />
                <span className="text-slate-200">PostgreSQL</span>
                <span className="text-slate-400 text-[10px]">Ledger</span>
              </div>
            </Tooltip>

            {/* WebSocket */}
            <Tooltip content="Live bidirectional WebSocket streaming telemetry at 1 Hz" position="bottom">
              <div className="flex items-center gap-1.5 cursor-help">
                <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400/50" />
                <span className="text-slate-200">WebSocket</span>
                <span className="text-slate-400 text-[10px]">1Hz</span>
              </div>
            </Tooltip>

            {/* ML Engine */}
            <Tooltip content="1D-CNN Autoencoder + Isolation Forest local inference" position="bottom">
              <div className="flex items-center gap-1.5 cursor-help">
                <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400/50" />
                <span className="text-slate-200">ML Engine</span>
                <span className="text-teal-400 font-bold text-[10px]">{latencyMs}ms</span>
              </div>
            </Tooltip>
          </div>

          {/* Right: Offline / WAN Status Slot */}
          <div className="flex items-center gap-3">
            {isCloudOutage ? (
              <Badge variant="offline" size="sm" pulseDot>
                OFFLINE — EDGE STANDALONE ACTIVE
              </Badge>
            ) : (
              <div className="flex items-center gap-1.5 text-slate-400 text-[10px]">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                <span>Cloud Sync Live</span>
              </div>
            )}
          </div>
        </div>

        {/* 4. Persistent Cloud Outage Banner when Active */}
        {isCloudOutage && (
          <div className="bg-amber-500 text-slate-950 px-6 py-2 flex items-center justify-between text-xs font-semibold border-b border-amber-600 shadow-sm">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-slate-950 shrink-0" />
              <span>Local monitoring active — cloud sync paused. 100% deterministic safety path running on edge.</span>
            </div>
            <button
              type="button"
              onClick={toggleCloudOutage}
              className="text-[11px] underline font-bold hover:text-white transition-colors"
            >
              Resume Cloud Sync
            </button>
          </div>
        )}

        {/* 5. Main View Content Body */}
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
};

export default AppShell;
