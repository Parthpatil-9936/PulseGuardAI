import React from 'react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  CartesianGrid, 
  LineChart, 
  Line, 
  Cell,
  AreaChart,
  Area
} from 'recharts';
import { 
  Users, 
  ShieldAlert, 
  ArrowLeftRight, 
  Clock, 
  TrendingUp, 
  Activity, 
  Calendar,
  CheckCircle2,
  FileSpreadsheet
} from 'lucide-react';
import { Badge, Button } from '../../components/ui';

export const AnalyticsDashboard = () => {
  // Alert counts by tier (Tier-colored bar chart data)
  const tierAlertData = [
    { tier: 'Tier 1 (Critical)', count: 6, fill: '#EF4444', desc: 'Hard safety threshold breaches' },
    { tier: 'Tier 2 (Warning)', count: 24, fill: '#F59E0B', desc: 'Predictive anomaly score >0.5' },
    { tier: 'Tier 3 (Advisory)', count: 48, fill: '#94A3B8', desc: 'Lead off / baseline drifts' },
  ];

  // 24-hour ward anomaly distribution
  const hourlyAnomalyData = [
    { hour: '00:00', anomalies: 2, avgResponseSec: 42 },
    { hour: '04:00', anomalies: 1, avgResponseSec: 48 },
    { hour: '08:00', anomalies: 8, avgResponseSec: 32 },
    { hour: '12:00', anomalies: 14, avgResponseSec: 28 },
    { hour: '16:00', anomalies: 11, avgResponseSec: 34 },
    { hour: '20:00', anomalies: 5, avgResponseSec: 39 },
  ];

  // Transfer activity breakdown
  const transferStats = [
    { type: 'Specialist Step-Up', count: 12 },
    { type: 'Shift Handover', count: 18 },
    { type: 'ICU Step-Down', count: 7 },
    { type: 'Code Team Handoff', count: 3 },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              Ward Analytics & Quality Assurance
            </h1>
            <span className="text-[11px] font-semibold bg-slate-100 text-slate-700 px-2 py-0.5 rounded-full border border-slate-200">
              Reporting Mode
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Rolling 24-hour clinical quality metrics • Alarm cascade audits & response latencies
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" icon={FileSpreadsheet}>
            Export Audit CSV
          </Button>
        </div>
      </div>

      {/* KPI Cards (Clean, light slate, data-dense) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1 */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Active Patients</span>
            <Users className="w-4 h-4 text-[#0EA5B7]" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="vital-number text-3xl font-extrabold text-slate-900">9</span>
            <span className="text-xs text-slate-400 font-medium">/ 10 Beds (90%)</span>
          </div>
          <span className="text-[11px] text-emerald-600 font-medium flex items-center gap-1">
            <TrendingUp className="w-3 h-3" /> 1 Bed Available
          </span>
        </div>

        {/* Metric 2 */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Total Alerts (24h)</span>
            <ShieldAlert className="w-4 h-4 text-amber-500" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="vital-number text-3xl font-extrabold text-slate-900">78</span>
            <span className="text-xs text-red-600 font-semibold font-mono">6 Tier 1</span>
          </div>
          <span className="text-[11px] text-slate-500">
            92% False Alarm Suppression by ML
          </span>
        </div>

        {/* Metric 3 */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Avg Ack Response</span>
            <Clock className="w-4 h-4 text-blue-500" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="vital-number text-3xl font-extrabold text-slate-900">34s</span>
            <span className="text-xs text-emerald-600 font-semibold">-12s vs ward target</span>
          </div>
          <span className="text-[11px] text-slate-500">
            Tier 1 response median: 14s
          </span>
        </div>

        {/* Metric 4 */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Transfer Velocity</span>
            <ArrowLeftRight className="w-4 h-4 text-purple-500" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="vital-number text-3xl font-extrabold text-slate-900">40</span>
            <span className="text-xs text-slate-400 font-medium">Handovers</span>
          </div>
          <span className="text-[11px] text-emerald-600 font-medium">
            100% Atomic Ledger Sync
          </span>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 1: Alert Counts by Tier (Bar Chart with exact Tier colors) */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-900 tracking-tight">
                Alert Volume Breakdown by Severity Tier
              </h3>
              <p className="text-xs text-slate-400">Tier 1 Red (Life-Threatening), Tier 2 Amber (Anomaly), Tier 3 Muted</p>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={tierAlertData} margin={{ top: 20, right: 20, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
                <XAxis dataKey="tier" tick={{ fontSize: 11, fill: '#64748B' }} />
                <YAxis tick={{ fontSize: 11, fill: '#94A3B8' }} />
                <Tooltip
                  formatter={(val, name, item) => [`${val} Events`, item.payload.desc]}
                  contentStyle={{ borderRadius: 12, border: '1px solid #E2E8F0', fontSize: 12 }}
                />
                <Bar dataKey="count" radius={[8, 8, 0, 0]}>
                  {tierAlertData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: 24h Anomaly & Response Time Curve */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-900 tracking-tight">
                24h Anomaly Volume & Response Time Curve
              </h3>
              <p className="text-xs text-slate-400">Clinician bedside acknowledgment latency</p>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={hourlyAnomalyData} margin={{ top: 20, right: 20, left: -20, bottom: 5 }}>
                <defs>
                  <linearGradient id="anomalyGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0EA5B7" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#0EA5B7" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
                <XAxis dataKey="hour" tick={{ fontSize: 11, fill: '#64748B' }} />
                <YAxis tick={{ fontSize: 11, fill: '#94A3B8' }} />
                <Tooltip contentStyle={{ borderRadius: 12, border: '1px solid #E2E8F0', fontSize: 12 }} />
                <Area 
                  type="monotone" 
                  dataKey="anomalies" 
                  name="Detected Anomalies" 
                  stroke="#0EA5B7" 
                  strokeWidth={2.5}
                  fillOpacity={1} 
                  fill="url(#anomalyGradient)" 
                />
                <Line 
                  type="monotone" 
                  dataKey="avgResponseSec" 
                  name="Avg Response (sec)" 
                  stroke="#3B82F6" 
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
