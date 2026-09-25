import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

const TransferContext = createContext(null);

const API_BASE_URL = 'http://127.0.0.1:8000';

const DOCTOR_MAP = {
  usr_doc_01: 'Dr. Sarah Chen, MD',
  usr_doc_02: 'Dr. Marcus Vance, MD',
  usr_doc_03: 'Dr. Elena Rostova, MD',
  usr_adm_01: 'Alex Rivera',
};

const PATIENT_MAP = {
  pat_01: { name: 'Eleanor Vance', bed: '01' },
  pat_02: { name: 'Marcus Sterling', bed: '02' },
  pat_03: { name: 'Harold Gomez', bed: '03' },
  pat_04: { name: 'Julian Drake', bed: '04' },
  pat_05: { name: 'Rosa Martinez', bed: '05' },
  pat_06: { name: 'Thomas Wright', bed: '06' },
  pat_07: { name: 'Aaliyah Khan', bed: '07' },
  pat_08: { name: 'Robert Lang', bed: '08' },
  pat_09: { name: 'Clara Oswald', bed: '09' },
  pat_10: { name: 'David Zhang', bed: '10' },
};

const INITIAL_TRANSFERS = [
  {
    id: 'tr_101',
    patientName: 'Julian Drake',
    bedId: '04',
    fromDoctor: 'Dr. Sarah Chen, MD',
    toDoctor: 'Dr. Marcus Vance, MD',
    reason: 'Rapidly deteriorating ARDS secondary to septic shock. Requires urgent pulmonology step-up and evaluation for veno-venous ECMO cannulation.',
    priority: 'Urgent',
    status: 'Pending',
    timestamp: '45 mins ago',
    requestedAt: Date.now() - 2700000,
  },
  {
    id: 'tr_102',
    patientName: 'Clara Oswald',
    bedId: '09',
    fromDoctor: 'Dr. Elena Rostova, MD',
    toDoctor: 'Dr. Marcus Vance, MD',
    reason: 'Intracranial pressure normalized post-burr hole evacuation. Step-down transfer to medical ICU for pulmonary weaning and extubation protocol.',
    priority: 'Routine',
    status: 'Pending',
    timestamp: '2 hours ago',
    requestedAt: Date.now() - 7200000,
  },
  {
    id: 'tr_100',
    patientName: 'Eleanor Vance',
    bedId: '01',
    fromDoctor: 'Dr. Marcus Vance, MD',
    toDoctor: 'Dr. Sarah Chen, MD',
    reason: 'Post-CABG hemodynamic stabilization achieved. Primary cardiology step-down handover.',
    priority: 'Routine',
    status: 'Approved',
    timestamp: 'Yesterday, 04:30 PM',
    completedAt: Date.now() - 86400000,
  },
  {
    id: 'tr_099',
    patientName: 'Thomas Wright',
    bedId: '06',
    fromDoctor: 'Dr. Marcus Vance, MD',
    toDoctor: 'Dr. Sarah Chen, MD',
    reason: 'Transfer request to general cardiology service.',
    priority: 'Routine',
    status: 'Rejected',
    rejectionReason: 'Patient remains hypercapnic on BiPAP; arterial blood gas pH 7.28. Must remain in respiratory ICU.',
    timestamp: '2 days ago',
  }
];

export const TransferProvider = ({ children }) => {
  const [transfers, setTransfers] = useState(INITIAL_TRANSFERS);
  const [toastMessage, setToastMessage] = useState(null);

  const showToast = (message) => {
    setToastMessage(message);
    setTimeout(() => {
      setToastMessage(null);
    }, 4000);
  };

  const getAuthHeaders = () => {
    const token = localStorage.getItem('pulseguard_token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
  };

  const loadTransfersFromBackend = useCallback(async () => {
    try {
      const resp = await fetch(`${API_BASE_URL}/transfers`, {
        headers: getAuthHeaders()
      });
      if (resp.ok) {
        const data = await resp.json();
        if (Array.isArray(data) && data.length > 0) {
          const mapped = data.map(t => {
            const pInfo = PATIENT_MAP[t.patient_id] || { name: `Patient ${t.patient_id}`, bed: '01' };
            const fromDoc = DOCTOR_MAP[t.from_doctor_id] || t.from_doctor_id;
            const toDoc = DOCTOR_MAP[t.to_doctor_id] || t.to_doctor_id;
            const capStatus = t.status.charAt(0).toUpperCase() + t.status.slice(1);
            return {
              id: t.id,
              patientName: pInfo.name,
              bedId: pInfo.bed,
              fromDoctor: fromDoc,
              toDoctor: toDoc,
              reason: t.reason,
              priority: t.priority || 'Routine',
              status: capStatus,
              rejectionReason: t.rejection_reason,
              timestamp: new Date(t.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
              requestedAt: new Date(t.created_at).getTime(),
            };
          });
          setTransfers(mapped);
        }
      }
    } catch (e) {
      // Backend not yet ready or offline; retain current state
    }
  }, []);

  useEffect(() => {
    loadTransfersFromBackend();
  }, [loadTransfersFromBackend]);

  const requestTransfer = async ({ patientName, bedId, fromDoctor, toDoctor, reason, priority = 'Routine' }) => {
    // Reverse-lookup patient ID
    const pEntry = Object.entries(PATIENT_MAP).find(([_, v]) => v.bed === bedId || v.name === patientName);
    const patientId = pEntry ? pEntry[0] : 'pat_04';

    // Reverse-lookup doctor ID
    const dEntry = Object.entries(DOCTOR_MAP).find(([_, name]) => name === toDoctor);
    const toDoctorId = dEntry ? dEntry[0] : 'usr_doc_02';

    // Optimistic UI update
    const newTransfer = {
      id: `tr_${Date.now()}`,
      patientName,
      bedId,
      fromDoctor,
      toDoctor,
      reason,
      priority,
      status: 'Pending',
      timestamp: 'Just now',
      requestedAt: Date.now(),
    };

    setTransfers(prev => [newTransfer, ...prev]);
    showToast(`Transfer requested for ${patientName} to ${toDoctor}`);

    // Call backend API
    try {
      const resp = await fetch(`${API_BASE_URL}/transfers`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        },
        body: JSON.stringify({
          patient_id: patientId,
          to_doctor_id: toDoctorId,
          reason,
          priority
        })
      });
      if (resp.ok) {
        await loadTransfersFromBackend();
      }
    } catch (err) {
      console.warn('Backend transfer creation offline:', err);
    }

    return newTransfer;
  };

  const approveTransfer = async (transferId) => {
    // Optimistic UI update
    setTransfers(prev => prev.map(t => {
      if (t.id === transferId) {
        return {
          ...t,
          status: 'Approved',
          approvedAt: 'Just now',
        };
      }
      return t;
    }));
    showToast('Transfer request approved. Patient roster updated.');

    // Call backend API
    try {
      const resp = await fetch(`${API_BASE_URL}/transfers/${transferId}/approve`, {
        method: 'POST',
        headers: getAuthHeaders()
      });
      if (resp.ok) {
        await loadTransfersFromBackend();
      }
    } catch (err) {
      console.warn('Backend transfer approval offline:', err);
    }
  };

  const rejectTransfer = async (transferId, rejectionReason) => {
    // Optimistic UI update
    setTransfers(prev => prev.map(t => {
      if (t.id === transferId) {
        return {
          ...t,
          status: 'Rejected',
          rejectionReason,
          rejectedAt: 'Just now',
        };
      }
      return t;
    }));
    showToast('Transfer request rejected.');

    // Call backend API
    try {
      const resp = await fetch(`${API_BASE_URL}/transfers/${transferId}/reject`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        },
        body: JSON.stringify({ reason: rejectionReason })
      });
      if (resp.ok) {
        await loadTransfersFromBackend();
      }
    } catch (err) {
      console.warn('Backend transfer rejection offline:', err);
    }
  };

  return (
    <TransferContext.Provider value={{
      transfers,
      requestTransfer,
      approveTransfer,
      rejectTransfer,
      toastMessage,
      showToast,
      refreshTransfers: loadTransfersFromBackend
    }}>
      {children}
    </TransferContext.Provider>
  );
};

export const useTransfer = () => {
  const context = useContext(TransferContext);
  if (!context) {
    throw new Error('useTransfer must be used within a TransferProvider');
  }
  return context;
};

export default TransferContext;
