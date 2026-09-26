import React, { useState, useEffect } from 'react';
import { 
  KeyRound, 
  ShieldCheck, 
  CheckCircle2, 
  XCircle, 
  RefreshCw, 
  Search, 
  Filter, 
  FileCode, 
  Lock, 
  AlertTriangle,
  Fingerprint
} from 'lucide-react';
import { Button, Badge, Input } from '../../components/ui';

export const AuditLogViewer = () => {
  const [logs, setLogs] = useState([
    {
      id: 'blk_1420',
      timestamp: '2026-09-25 10:44:12',
      action: 'CRITICAL_ALERT_ACKNOWLEDGED',
      actor: 'Dr. Sarah Chen, MD',
      role: 'doctor',
      patient: 'Julian Drake (Bed 04)',
    },
    {
      id: 'blk_1419',
      timestamp: '2026-09-25 10:42:01',
      action: 'TIER1_ALARM_CASCADE_TRIGGERED',
      actor: 'Deterministic Edge Engine',
      role: 'system',
      patient: 'Julian Drake (Bed 04)',
    },
    {
      id: 'blk_1418',
      timestamp: '2026-09-25 10:15:30',
      action: 'TRANSFER_REQUEST_SUBMITTED',
      actor: 'Dr. Sarah Chen, MD',
      role: 'doctor',
      patient: 'Julian Drake (Bed 04)',
    },
    {
      id: 'blk_1417',
      timestamp: '2026-09-25 09:30:15',
      action: 'EMERGENCY_BREAK_GLASS_GRANTED',
      actor: 'Alex Rivera',
      role: 'admin',
      patient: 'Marcus Sterling (Bed 02)',
    },
    {
      id: 'blk_1416',
      timestamp: '2026-09-25 08:30:00',
      action: 'PHYSICIAN_NOTE_RECORDED',
      actor: 'Dr. Marcus Vance, MD',
      role: 'doctor',
      patient: 'Julian Drake (Bed 04)',
    },
    {
      id: 'blk_1415',
      timestamp: '2026-09-25 07:45:10',
      action: 'ALARM_MUTE_CLAMPED_300S',
      actor: 'Dr. Sarah Chen, MD',
      role: 'doctor',
      patient: 'Thomas Wright (Bed 06)',
    },
  ]);

  const [verifying, setVerifying] = useState(false);

  const [search, setSearch] = useState('');

  useEffect(() => {
    const fetchLiveLogs = async () => {
      try {
        const token = localStorage.getItem('pulseguard_token');
        const res = await fetch('http://127.0.0.1:8000/audit-logs', {
          headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        });
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data) && data.length > 0) {
            setLogs(data.map(item => ({
              id: `blk_${item.seq_id}`,
              timestamp: item.timestamp.replace('T', ' ').substring(0, 19),
              action: item.action,
              actor: item.clinician_id === 'usr_doc_01' ? 'Dr. Sarah Chen, MD' :
                     item.clinician_id === 'usr_doc_02' ? 'Dr. Marcus Vance, MD' :
                     item.clinician_id === 'usr_doc_03' ? 'Dr. Elena Rostova, MD' :
                     item.clinician_id === 'usr_adm_01' ? 'Alex Rivera' : 'Deterministic Edge Engine',
              role: item.clinician_id === 'usr_adm_01' ? 'admin' : item.clinician_id ? 'doctor' : 'system',
              patient: item.bed_id ? `Bed ${item.bed_id}` : 'Ward Scope',

            })));
          }
        }
      } catch (err) {
        // Fallback to local default mock logs
      }
    };
    fetchLiveLogs();
  }, []);



  const filteredLogs = logs.filter(l => {
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return l.action.toLowerCase().includes(q) || l.actor.toLowerCase().includes(q) || l.patient.toLowerCase().includes(q);
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              Audit Ledger
            </h1>
            <Badge variant="normal" size="sm">
              DPDP Act Sec. 8(3)
            </Badge>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Audit log linking all clinical alarms, muting actions, transfers, and break-glass grants
          </p>
        </div>

      </div>

      {/* Ledger Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-3.5 px-4">Block #</th>
                <th className="py-3.5 px-4">Timestamp</th>
                <th className="py-3.5 px-4">Action</th>
                <th className="py-3.5 px-4">Actor</th>
                <th className="py-3.5 px-4">Patient / Bed</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700 font-mono">
              {filteredLogs.map((log) => {
                const isSystem = log.role === 'system';
                const isAlert = log.action.includes('ALERT') || log.action.includes('ALARM');

                return (
                  <tr key={log.id} className="hover:bg-slate-50/70 transition-colors font-sans">
                    <td className="py-3.5 px-4 font-mono font-bold text-[#0D8A9A]">
                      {log.id}
                    </td>
                    <td className="py-3.5 px-4 text-slate-500 text-[11px] font-mono">
                      {log.timestamp}
                    </td>
                    <td className="py-3.5 px-4 font-semibold text-slate-900">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-mono ${
                        isAlert ? 'bg-red-50 text-red-700' : 'bg-slate-100 text-slate-700'
                      }`}>
                        {log.action}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-medium text-slate-800">
                      {log.actor}
                    </td>
                    <td className="py-3.5 px-4 font-medium text-slate-600">
                      {log.patient}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AuditLogViewer;
