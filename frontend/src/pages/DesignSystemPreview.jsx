import React, { useState } from 'react';
import { 
  HeartPulse, 
  Activity, 
  ShieldAlert, 
  CheckCircle2, 
  AlertTriangle, 
  Info, 
  Layers, 
  Type, 
  Palette, 
  Box, 
  Stethoscope,
  Sparkles,
  ExternalLink,
  ChevronRight,
  Search,
  Bell
} from 'lucide-react';
import { 
  Button, 
  Badge, 
  Card, 
  CardHeader, 
  CardTitle, 
  CardDescription, 
  CardContent, 
  CardFooter,
  Modal, 
  ModalFooter,
  Input, 
  Select, 
  Avatar, 
  Tooltip, 
  GradientMesh 
} from '../components/ui';

export const DesignSystemPreview = ({ onNavigateToApp }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalType, setModalType] = useState('standard'); // 'standard' | 'critical'
  const [selectedRole, setSelectedRole] = useState('doctor');
  const [testInputValue, setTestInputValue] = useState('');

  return (
    <div className="min-h-screen bg-[#F8FAFC] pb-24 text-slate-900">
      {/* Sticky Top Header */}
      <header className="sticky top-0 z-40 glass-panel border-b border-white/60 px-6 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-[#0D8A9A] to-[#0EA5B7] flex items-center justify-center text-white shadow-md shadow-teal-500/20">
            <HeartPulse className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-slate-900">PulseGuard-AI</h1>
              <span className="text-[11px] font-semibold bg-teal-50 text-[#0D8A9A] border border-teal-200/80 px-2 py-0.5 rounded-full">
                Design System v3.0
              </span>
            </div>
            <p className="text-xs text-slate-500">Hospital Ward Monitoring • Deterministic Edge-Triage System</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {onNavigateToApp && (
            <Button 
              variant="primary" 
              size="sm" 
              icon={ExternalLink} 
              iconPosition="right"
              onClick={onNavigateToApp}
            >
              Launch Live Application
            </Button>
          )}
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-6 pt-8 space-y-12">
        {/* Intro Banner */}
        <section className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-slate-900 via-slate-800 to-teal-950 text-white p-8 shadow-xl">
          <div className="relative z-10 max-w-2xl space-y-3">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/20 border border-teal-400/30 text-teal-300 text-xs font-semibold">
              <Sparkles className="w-3.5 h-3.5" /> Phase 1 Foundations Verified
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">Clinical Design System & Token Architecture</h2>
            <p className="text-slate-300 text-sm leading-relaxed">
              Engineered specifically for high-stress critical care environments. Every token prioritizes rapid glanceability, unmissable alert hierarchy, and fail-safe legibility without fatigue.
            </p>
          </div>
          <div className="absolute right-6 top-1/2 -translate-y-1/2 hidden lg:flex items-center gap-4 opacity-15">
            <HeartPulse className="w-64 h-64 text-teal-400" />
          </div>
        </section>

        {/* Section 1: Color Tokens */}
        <section className="space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
            <Palette className="w-5 h-5 text-[#0EA5B7]" />
            <h2 className="text-lg font-bold text-slate-900">1. Color Tokens & Semantic Spectrum</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Base Tokens */}
            <Card variant="elevated">
              <CardHeader>
                <CardTitle>Base Surfaces</CardTitle>
                <CardDescription>Ground plane and glass surfaces</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="p-3 rounded-xl bg-[#F8FAFC] border border-slate-200 flex items-center justify-between">
                  <div>
                    <span className="text-xs font-semibold block text-slate-800">Background</span>
                    <span className="text-[11px] font-mono text-slate-500">#F8FAFC</span>
                  </div>
                  <div className="w-7 h-7 rounded-lg bg-[#F8FAFC] border border-slate-300 shadow-sm" />
                </div>

                <div className="p-3 rounded-xl bg-white border border-slate-200 flex items-center justify-between">
                  <div>
                    <span className="text-xs font-semibold block text-slate-800">Surface Card</span>
                    <span className="text-[11px] font-mono text-slate-500">#FFFFFF</span>
                  </div>
                  <div className="w-7 h-7 rounded-lg bg-white border border-slate-200 shadow" />
                </div>

                <div className="p-3 rounded-xl glass-panel flex items-center justify-between">
                  <div>
                    <span className="text-xs font-semibold block text-slate-800">Surface Glass</span>
                    <span className="text-[11px] font-mono text-slate-500">rgba(255,255,255,0.6)</span>
                  </div>
                  <div className="w-7 h-7 rounded-lg glass-panel" />
                </div>
              </CardContent>
            </Card>

            {/* Primary Teal Tokens */}
            <Card variant="elevated">
              <CardHeader>
                <CardTitle>Primary Brand (Teal)</CardTitle>
                <CardDescription>Normal vitals & primary actions</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="p-3 rounded-xl bg-teal-50 border border-teal-200 flex items-center justify-between">
                  <div>
                    <span className="text-xs font-semibold block text-teal-900">Teal 500 (Primary)</span>
                    <span className="text-[11px] font-mono text-teal-700">#0EA5B7</span>
                  </div>
                  <div className="w-7 h-7 rounded-lg bg-[#0EA5B7] shadow-sm" />
                </div>

                <div className="p-3 rounded-xl bg-teal-100/50 border border-teal-300 flex items-center justify-between">
                  <div>
                    <span className="text-xs font-semibold block text-teal-950">Teal 600 (Hover/Focus)</span>
                    <span className="text-[11px] font-mono text-teal-800">#0D8A9A</span>
                  </div>
                  <div className="w-7 h-7 rounded-lg bg-[#0D8A9A] shadow-sm" />
                </div>

                <div className="p-3 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-between">
                  <div>
                    <span className="text-xs font-semibold block text-blue-900">Secondary (Blue 500)</span>
                    <span className="text-[11px] font-mono text-blue-700">#3B82F6</span>
                  </div>
                  <div className="w-7 h-7 rounded-lg bg-[#3B82F6] shadow-sm" />
                </div>
              </CardContent>
            </Card>

            {/* Alert Tier Tokens */}
            <Card variant="elevated">
              <CardHeader>
                <CardTitle>Clinical Alert Tiers</CardTitle>
                <CardDescription>ECRI / ICU triage standard</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="p-3 rounded-xl bg-red-50 border border-red-200 flex items-center justify-between">
                  <div>
                    <span className="text-xs font-semibold block text-red-900">Tier 1: Critical Red</span>
                    <span className="text-[11px] font-mono text-red-700">#EF4444 • Life-Threatening</span>
                  </div>
                  <div className="w-7 h-7 rounded-lg bg-[#EF4444] shadow-sm shadow-red-500/30 animate-pulse" />
                </div>

                <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-between">
                  <div>
                    <span className="text-xs font-semibold block text-amber-900">Tier 2: Warning Amber</span>
                    <span className="text-[11px] font-mono text-amber-700">#F59E0B • Abnormal Trend</span>
                  </div>
                  <div className="w-7 h-7 rounded-lg bg-[#F59E0B] shadow-sm shadow-amber-500/30" />
                </div>

                <div className="p-3 rounded-xl bg-slate-100 border border-slate-200 flex items-center justify-between">
                  <div>
                    <span className="text-xs font-semibold block text-slate-800">Tier 3: Muted Slate</span>
                    <span className="text-[11px] font-mono text-slate-600">#94A3B8 • Advisory</span>
                  </div>
                  <div className="w-7 h-7 rounded-lg bg-[#94A3B8] shadow-sm" />
                </div>
              </CardContent>
            </Card>

            {/* Typography Colors */}
            <Card variant="elevated">
              <CardHeader>
                <CardTitle>Slate Text Scale</CardTitle>
                <CardDescription>Strict contrast WCAG AAA</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                  <div>
                    <span className="text-xs font-bold block text-slate-900">Slate 900 (Headings)</span>
                    <span className="text-[11px] font-mono text-slate-500">#0F172A</span>
                  </div>
                  <span className="text-xs font-bold text-slate-900">Aa</span>
                </div>

                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                  <div>
                    <span className="text-xs font-semibold block text-slate-600">Slate 600 (Body)</span>
                    <span className="text-[11px] font-mono text-slate-500">#475569</span>
                  </div>
                  <span className="text-xs font-medium text-slate-600">Aa</span>
                </div>

                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                  <div>
                    <span className="text-xs font-semibold block text-slate-400">Slate 400 (Muted)</span>
                    <span className="text-[11px] font-mono text-slate-400">#94A3B8</span>
                  </div>
                  <span className="text-xs font-normal text-slate-400">Aa</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* Section 2: Depth System */}
        <section className="space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
            <Layers className="w-5 h-5 text-[#0EA5B7]" />
            <h2 className="text-lg font-bold text-slate-900">2. Depth System (Glass + Soft Elevation Hybrid)</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* .glass-panel */}
            <div className="glass-panel rounded-2xl p-6 relative overflow-hidden">
              <div className="absolute top-0 right-0 p-3">
                <Badge variant="normal" size="sm">.glass-panel</Badge>
              </div>
              <h3 className="font-semibold text-slate-900 text-sm mb-1">Glassmorphic Surface</h3>
              <p className="text-xs text-slate-600 mb-4 leading-relaxed">
                <code className="bg-white/80 px-1.5 py-0.5 rounded text-[11px]">backdrop-blur-lg</code>, <code className="bg-white/80 px-1.5 py-0.5 rounded text-[11px]">bg-white/60</code>, and layered ambient drop shadow for subtle visual hierarchy without visual clutter.
              </p>
              <div className="p-3 bg-white/70 rounded-xl border border-white/60 flex items-center gap-2">
                <Activity className="w-4 h-4 text-[#0EA5B7]" />
                <span className="text-xs font-medium text-slate-800">Layered translucent card element</span>
              </div>
            </div>

            {/* .card-elevated */}
            <div className="card-elevated p-6 relative overflow-hidden">
              <div className="absolute top-0 right-0 p-3">
                <Badge variant="normal" size="sm">.card-elevated</Badge>
              </div>
              <h3 className="font-semibold text-slate-900 text-sm mb-1">Raised Solid Card</h3>
              <p className="text-xs text-slate-600 mb-4 leading-relaxed">
                Solid pure white background with dual-layer shadow (soft ambient + tight contact) simulating raised tactile clinical depth.
              </p>
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-teal-600" />
                <span className="text-xs font-medium text-slate-800">Dual-layer shadow simulation</span>
              </div>
            </div>

            {/* hover-lift */}
            <div className="card-elevated hover-lift p-6 relative overflow-hidden cursor-pointer group">
              <div className="absolute top-0 right-0 p-3">
                <Badge variant="doctor" size="sm">.hover-lift</Badge>
              </div>
              <h3 className="font-semibold text-slate-900 text-sm mb-1 group-hover:text-[#0EA5B7] transition-colors">
                Hover-Lift Utility
              </h3>
              <p className="text-xs text-slate-600 mb-4 leading-relaxed">
                Hover over this card to witness the subtle <code className="bg-slate-100 px-1.5 py-0.5 rounded text-[11px]">-translate-y-1</code> and elevated shadow. Used on all clickable bed tiles and primary buttons.
              </p>
              <div className="p-3 bg-teal-50/60 rounded-xl border border-teal-100 flex items-center justify-between">
                <span className="text-xs font-semibold text-teal-900">Try hovering me</span>
                <ChevronRight className="w-4 h-4 text-[#0EA5B7] transition-transform group-hover:translate-x-1" />
              </div>
            </div>
          </div>

          {/* Gradient Mesh Demonstration */}
          <div className="relative rounded-2xl overflow-hidden border border-slate-200/80 shadow-sm p-6 bg-slate-50">
            <h3 className="font-bold text-slate-900 text-sm mb-1">Animated Gradient-Mesh Demonstration</h3>
            <p className="text-xs text-slate-500 mb-4">
              Soft teal-to-blue radial blobs with low opacity and continuous drifting CSS keyframes for auth, splash, and background ambiance:
            </p>
            <div className="h-32 rounded-xl overflow-hidden relative border border-slate-200 bg-white">
              <div className="absolute inset-0 bg-[#F8FAFC]">
                <div className="absolute -top-10 -left-10 w-44 h-44 rounded-full bg-primary-500/25 blur-3xl animate-mesh-drift" />
                <div className="absolute -bottom-10 right-10 w-44 h-44 rounded-full bg-secondary-500/20 blur-3xl animate-mesh-drift" style={{ animationDirection: 'reverse' }} />
              </div>
              <div className="relative h-full flex items-center justify-center">
                <div className="glass-panel px-6 py-2.5 rounded-xl border border-white/60 shadow-sm flex items-center gap-3">
                  <HeartPulse className="w-5 h-5 text-[#0EA5B7] animate-pulse" />
                  <span className="text-xs font-bold text-slate-800">Dynamic Radial Drifting Atmosphere</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Section 3: Typography */}
        <section className="space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
            <Type className="w-5 h-5 text-[#0EA5B7]" />
            <h2 className="text-lg font-bold text-slate-900">3. Typography Scale & Clinical Vital Readability</h2>
          </div>

          <Card variant="elevated">
            <CardHeader>
              <CardTitle>Inter Font Hierarchy (Never Thin Weights on Vitals)</CardTitle>
              <CardDescription>
                Designed for high cognitive load. High-contrast medium/semibold weights ensure zero misreads during emergencies.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="p-4 bg-slate-50/70 rounded-xl space-y-1">
                  <span className="text-[11px] font-mono text-slate-400">text-4xl • semibold</span>
                  <div className="vital-number text-4xl text-slate-900">128<span className="text-base text-slate-400 font-normal ml-1">BPM</span></div>
                  <p className="text-xs text-slate-500 font-medium">Critical Heart Rate Readout</p>
                </div>

                <div className="p-4 bg-slate-50/70 rounded-xl space-y-1">
                  <span className="text-[11px] font-mono text-slate-400">text-3xl • bold</span>
                  <div className="vital-number text-3xl text-teal-600">98%<span className="text-xs text-slate-400 font-normal ml-1">SpO2</span></div>
                  <p className="text-xs text-slate-500 font-medium">Normal Oxygen Saturation</p>
                </div>

                <div className="p-4 bg-slate-50/70 rounded-xl space-y-1">
                  <span className="text-[11px] font-mono text-slate-400">text-2xl • semibold</span>
                  <div className="vital-number text-2xl text-slate-900">124/82<span className="text-xs text-slate-400 font-normal ml-1">mmHg</span></div>
                  <p className="text-xs text-slate-500 font-medium">Non-Invasive Blood Pressure</p>
                </div>

                <div className="p-4 bg-slate-50/70 rounded-xl space-y-1">
                  <span className="text-[11px] font-mono text-slate-400">text-lg / text-xs scale</span>
                  <h4 className="text-lg font-bold text-slate-900">Bed 04 • J. DOE</h4>
                  <p className="text-xs text-slate-600">Post-op Cardiac Bypass • Day 2</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </section>

        {/* Section 4: UI Components Library */}
        <section className="space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
            <Box className="w-5 h-5 text-[#0EA5B7]" />
            <h2 className="text-lg font-bold text-slate-900">4. Interactive Component Gallery</h2>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Buttons */}
            <Card variant="elevated">
              <CardHeader>
                <CardTitle>Buttons (with Lift-on-Hover)</CardTitle>
                <CardDescription>Primary, secondary, danger, and glass variants with responsive states</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex flex-wrap items-center gap-3">
                  <Button variant="primary" size="md">Primary Teal</Button>
                  <Button variant="secondary" size="md">Secondary Blue</Button>
                  <Button variant="danger" size="md">Danger Tier 1</Button>
                  <Button variant="outline" size="md">Outline</Button>
                  <Button variant="ghost" size="md">Ghost</Button>
                </div>

                <div className="flex flex-wrap items-center gap-3">
                  <Button variant="primary" size="sm">Small</Button>
                  <Button variant="primary" size="md">Medium</Button>
                  <Button variant="primary" size="lg">Large Clinical Action</Button>
                </div>

                <div className="flex flex-wrap items-center gap-3">
                  <Button variant="primary" size="md" icon={HeartPulse}>With Icon</Button>
                  <Button variant="danger" size="md" loading={true}>Processing</Button>
                  <Button variant="secondary" size="md" disabled={true}>Disabled</Button>
                </div>
              </CardContent>
            </Card>

            {/* Badges */}
            <Card variant="elevated">
              <CardHeader>
                <CardTitle>Badges & Status Pills</CardTitle>
                <CardDescription>Alert tiers and clinical roles with status dots</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <span className="text-xs font-semibold text-slate-400 block mb-2 uppercase tracking-wider">Clinical Tiers</span>
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant="tier1" dot pulseDot>Tier 1: Critical (Pulsing)</Badge>
                    <Badge variant="tier2" dot>Tier 2: Warning</Badge>
                    <Badge variant="normal" dot>Normal Telemetry</Badge>
                    <Badge variant="tier3">Tier 3: Muted</Badge>
                  </div>
                </div>

                <div>
                  <span className="text-xs font-semibold text-slate-400 block mb-2 uppercase tracking-wider">Clinician Roles</span>
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant="doctor" dot>Dr. Attending</Badge>
                    <Badge variant="doctor" dot>Dr. Fellow</Badge>
                    <Badge variant="admin" dot>System Admin</Badge>
                  </div>
                </div>

                <div>
                  <span className="text-xs font-semibold text-slate-400 block mb-2 uppercase tracking-wider">System State</span>
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant="online" dot>FastAPI Connected</Badge>
                    <Badge variant="edge" dot>Edge Local Buffer</Badge>
                    <Badge variant="offline" dot pulseDot>WAN Offline</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Form Inputs & Select */}
            <Card variant="elevated">
              <CardHeader>
                <CardTitle>Inputs & Clinical Selects</CardTitle>
                <CardDescription>Formatted for rapid entry with validation styling</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <Input 
                    label="Patient Search / Bed ID"
                    placeholder="e.g. Bed-04 or JD-982"
                    icon={Search}
                    value={testInputValue}
                    onChange={(e) => setTestInputValue(e.target.value)}
                  />

                  <Select
                    label="Assigned Clinician"
                    options={[
                      { value: 'chen', label: 'Dr. Sarah Chen (Cardiology)' },
                      { value: 'vance', label: 'Dr. Marcus Vance (ICU Director)' },
                      { value: 'rostova', label: 'Dr. Elena Rostova (Neuro ICU)' },
                    ]}
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <Input 
                    label="Emergency Override Reason"
                    placeholder="Clinical rationale required..."
                    helperText="Mandatory under DPDP Act Sec. 8(3)"
                  />

                  <Input 
                    label="Validation Error State"
                    defaultValue="Invalid SpO2 calibration value"
                    error="Value must be between 50% and 100%"
                  />
                </div>
              </CardContent>
            </Card>

            {/* Avatars & Tooltips */}
            <Card variant="elevated">
              <CardHeader>
                <CardTitle>Avatars & Accessible Tooltips</CardTitle>
                <CardDescription>Hover over avatars to trigger tooltip components</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <span className="text-xs font-semibold text-slate-400 block mb-3 uppercase tracking-wider">Avatar Sizes & Roles</span>
                  <div className="flex items-center gap-4">
                    <Tooltip content="System Administrator (Level 3 Clearance)" position="top">
                      <Avatar name="Admin Alex" role="admin" size="lg" status="online" />
                    </Tooltip>

                    <Tooltip content="Dr. Sarah Chen, MD • On-Duty Attending" position="top">
                      <Avatar name="Sarah Chen" role="doctor" size="md" status="online" />
                    </Tooltip>

                    <Tooltip content="Dr. Elena Rostova, MD • Neuro ICU" position="top">
                      <Avatar name="Elena Rostova" role="doctor" size="md" status="busy" />
                    </Tooltip>

                    <Tooltip content="Patient Bed 08 (J.R.)" position="top">
                      <Avatar name="James Ray" role="patient" size="sm" status="offline" />
                    </Tooltip>
                  </div>
                </div>

                <div>
                  <span className="text-xs font-semibold text-slate-400 block mb-2 uppercase tracking-wider">Tooltip Direction Matrix</span>
                  <div className="flex flex-wrap items-center gap-3">
                    <Tooltip content="Tooltip placed on Top" position="top">
                      <Button variant="outline" size="sm">Top Tooltip</Button>
                    </Tooltip>
                    <Tooltip content="Tooltip placed on Bottom" position="bottom">
                      <Button variant="outline" size="sm">Bottom Tooltip</Button>
                    </Tooltip>
                    <Tooltip content="Tooltip placed on Left" position="left">
                      <Button variant="outline" size="sm">Left Tooltip</Button>
                    </Tooltip>
                    <Tooltip content="Tooltip placed on Right" position="right">
                      <Button variant="outline" size="sm">Right Tooltip</Button>
                    </Tooltip>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* Section 5: Modal & Alert Takeover Preview */}
        <section className="space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
            <ShieldAlert className="w-5 h-5 text-red-500" />
            <h2 className="text-lg font-bold text-slate-900">5. Modal & Critical Alert Takeover</h2>
          </div>

          <Card variant="elevated">
            <CardHeader>
              <CardTitle>Glass Backdrop Modal Dialogs</CardTitle>
              <CardDescription>
                Test both standard confirmation modals and Phase 4 un-dismissible Tier 1 critical alarm takeovers
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-wrap items-center gap-4">
              <Button 
                variant="outline"
                onClick={() => {
                  setModalType('standard');
                  setIsModalOpen(true);
                }}
              >
                Open Standard Modal (Glass Backdrop)
              </Button>

              <Button 
                variant="danger"
                icon={ShieldAlert}
                onClick={() => {
                  setModalType('critical');
                  setIsModalOpen(true);
                }}
              >
                Simulate Tier 1 Full-Screen Alert Takeover
              </Button>
            </CardContent>
          </Card>
        </section>
      </main>

      {/* Interactive Modal instance */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={modalType === 'critical' ? 'CRITICAL TIER 1 ALERT — IMMEDIATE ATTENTION REQUIRED' : 'Confirm Clinical Action'}
        description={modalType === 'critical' ? 'Bed 04 • Acute Desaturation Event (SpO2: 78%)' : 'Please review and confirm before continuing'}
        criticalTier1={modalType === 'critical'}
        disableBackdropDismiss={modalType === 'critical'}
      >
        {modalType === 'critical' ? (
          <div className="space-y-4">
            <div className="p-4 bg-red-50 border border-red-200 rounded-xl">
              <div className="flex items-start gap-3">
                <ShieldAlert className="w-6 h-6 text-red-600 shrink-0 mt-0.5 animate-bounce" />
                <div className="space-y-1">
                  <h4 className="text-sm font-bold text-red-900">Deterministic Hard Threshold Breached</h4>
                  <p className="text-xs text-red-700 leading-relaxed">
                    SpO2 dropped below the unsuppressable safety barrier of 85.0%. Deterministic edge rule executed with zero WAN dependency.
                  </p>
                  <div className="pt-2 flex items-center gap-2">
                    <span className="text-xs font-mono font-bold bg-red-100 text-red-800 px-2 py-0.5 rounded">SpO2: 78%</span>
                    <span className="text-xs font-mono font-bold bg-red-100 text-red-800 px-2 py-0.5 rounded">HR: 134 BPM</span>
                  </div>
                </div>
              </div>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              This modal cannot be closed by clicking outside or pressing Escape. A licensed clinician must acknowledge this alert to silence the edge buzzer.
            </p>

            <ModalFooter>
              <Button
                variant="danger"
                size="lg"
                className="w-full justify-center"
                onClick={() => setIsModalOpen(false)}
              >
                Acknowledge Alert & Begin Bedside Response
              </Button>
            </ModalFooter>
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-sm text-slate-600">
              This standard modal demonstrates the glassmorphic background blur, soft borders, and responsive button layout.
            </p>
            <ModalFooter>
              <Button variant="ghost" onClick={() => setIsModalOpen(false)}>
                Cancel
              </Button>
              <Button variant="primary" onClick={() => setIsModalOpen(false)}>
                Confirm Action
              </Button>
            </ModalFooter>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default DesignSystemPreview;
