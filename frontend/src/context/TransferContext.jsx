import React, { createContext, useContext, useState } from 'react';

const TransferContext = createContext(null);

const INITIAL_TRANSFERS = [
  {
    id: 'tr_101',
    patientName: 'Julian Drake',
    bedId: '04',
    fromDoctor: 'Dr. Sarah Chen, MD',
    toDoctor: 'Dr. Marcus Vance, MD',
    reason: 'ICU step-up and advanced hemodynamic ECMO assessment required.',
    priority: 'Urgent',
    status: 'Pending', // 'Pending' | 'Approved' | 'Rejected' | 'Completed'
    timestamp: 'Today, 10:15 AM',
    requestedAt: Date.now() - 3600000,
  },
  {
    id: 'tr_100',
    patientName: 'Eleanor Vance',
    bedId: '01',
    fromDoctor: 'Dr. Marcus Vance, MD',
    toDoctor: 'Dr. Sarah Chen, MD',
    reason: 'Post-CABG telemetry step-down handover.',
    priority: 'Routine',
    status: 'Completed',
    timestamp: 'Yesterday, 04:30 PM',
    completedAt: Date.now() - 86400000,
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

  const requestTransfer = ({ patientName, bedId, fromDoctor, toDoctor, reason, priority = 'Routine' }) => {
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

    setTransfers([newTransfer, ...transfers]);
    showToast(`Transfer requested for ${patientName} to ${toDoctor}`);
    return newTransfer;
  };

  const approveTransfer = (transferId) => {
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
    showToast('Transfer request approved. Patient roster updated optimistically.');
  };

  const rejectTransfer = (transferId, rejectionReason) => {
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
  };

  return (
    <TransferContext.Provider value={{
      transfers,
      requestTransfer,
      approveTransfer,
      rejectTransfer,
      toastMessage,
      showToast
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
