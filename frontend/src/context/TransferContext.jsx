import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

const TransferContext = createContext(null);

const API_BASE_URL = 'http://127.0.0.1:8000';

export const TransferProvider = ({ children }) => {
  const [transfers, setTransfers] = useState([]);
  const [toastMessage, setToastMessage] = useState(null);
  const [loading, setLoading] = useState(true);

  const showToast = (message) => {
    setToastMessage(message);
    setTimeout(() => setToastMessage(null), 4000);
  };

  const getAuthHeaders = () => {
    const token = localStorage.getItem('pulseguard_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  const loadTransfersFromBackend = useCallback(async () => {
    const token = localStorage.getItem('pulseguard_token');
    if (!token) { setLoading(false); return; }
    try {
      const [tRes, pRes, uRes] = await Promise.all([
        fetch(`${API_BASE_URL}/transfers`, { headers: getAuthHeaders() }),
        fetch(`${API_BASE_URL}/patients`, { headers: getAuthHeaders() }).catch(() => ({ ok: false })),
        fetch(`${API_BASE_URL}/auth/users`, { headers: getAuthHeaders() }).catch(() => ({ ok: false })),
      ]);
      if (!tRes.ok) { setLoading(false); return; }
      const rawTransfers = await tRes.json();
      const rawPatients = pRes.ok ? await pRes.json() : [];
      const rawUsers = uRes.ok ? await uRes.json() : [];
      const patientMap = Object.fromEntries(rawPatients.map(p => [p.id, p]));
      const userMap = Object.fromEntries(rawUsers.map(u => [u.id, u]));
      const mapped = rawTransfers.map(t => {
        const patient = patientMap[t.patient_id] || null;
        const fromDoc = userMap[t.from_doctor_id] || null;
        const toDoc = userMap[t.to_doctor_id] || null;
        const capStatus = t.status ? t.status.charAt(0).toUpperCase() + t.status.slice(1) : 'Pending';
        return {
          id: t.id,
          patientId: t.patient_id,
          patientName: patient?.demographics?.name || t.patient_id,
          bedId: '—',
          fromDoctor: fromDoc?.name || t.from_doctor_id,
          fromDoctorId: t.from_doctor_id,
          toDoctor: toDoc?.name || t.to_doctor_id,
          toDoctorId: t.to_doctor_id,
          reason: t.reason,
          priority: t.priority || 'Routine',
          status: capStatus,
          rejectionReason: t.rejection_reason,
          timestamp: t.created_at ? new Date(t.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Unknown',
          requestedAt: t.created_at ? new Date(t.created_at).getTime() : Date.now(),
          completedAt: t.decided_at ? new Date(t.decided_at).getTime() : null,
        };
      });
      setTransfers(mapped);
    } catch (e) {
      console.warn('TransferContext: fetch failed', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadTransfersFromBackend(); }, [loadTransfersFromBackend]);

  const requestTransfer = async ({ patientId, patientName, bedId, fromDoctor, toDoctor, toDoctorId, reason, priority = 'Routine' }) => {
    const tempId = `tr_temp_${Date.now()}`;
    const optimistic = { id: tempId, patientId, patientName: patientName || patientId, bedId: bedId || '—', fromDoctor, toDoctor, toDoctorId, reason, priority, status: 'Pending', timestamp: 'Just now', requestedAt: Date.now() };
    setTransfers(prev => [optimistic, ...prev]);
    showToast(`Transfer requested for ${patientName || patientId} to ${toDoctor}`);
    try {
      const resp = await fetch(`${API_BASE_URL}/transfers`, { method: 'POST', headers: { 'Content-Type': 'application/json', ...getAuthHeaders() }, body: JSON.stringify({ patient_id: patientId, to_doctor_id: toDoctorId, reason, priority }) });
      if (resp.ok) await loadTransfersFromBackend();
    } catch (err) { console.warn('Transfer creation failed:', err); }
    return optimistic;
  };

  const approveTransfer = async (transferId) => {
    setTransfers(prev => prev.map(t => t.id === transferId ? { ...t, status: 'Approved', completedAt: Date.now() } : t));
    showToast('Transfer request approved. Patient roster updated.');
    try { const resp = await fetch(`${API_BASE_URL}/transfers/${transferId}/approve`, { method: 'POST', headers: getAuthHeaders() }); if (resp.ok) await loadTransfersFromBackend(); } catch (err) { console.warn(err); }
  };

  const rejectTransfer = async (transferId, rejectionReason) => {
    setTransfers(prev => prev.map(t => t.id === transferId ? { ...t, status: 'Rejected', rejectionReason } : t));
    showToast('Transfer request rejected.');
    try { const resp = await fetch(`${API_BASE_URL}/transfers/${transferId}/reject`, { method: 'POST', headers: { 'Content-Type': 'application/json', ...getAuthHeaders() }, body: JSON.stringify({ reason: rejectionReason }) }); if (resp.ok) await loadTransfersFromBackend(); } catch (err) { console.warn(err); }
  };

  return (
    <TransferContext.Provider value={{ transfers, loading, requestTransfer, approveTransfer, rejectTransfer, toastMessage, showToast, refreshTransfers: loadTransfersFromBackend }}>
      {children}
    </TransferContext.Provider>
  );
};

export const useTransfer = () => {
  const context = useContext(TransferContext);
  if (!context) throw new Error('useTransfer must be used within a TransferProvider');
  return context;
};

export default TransferContext;
