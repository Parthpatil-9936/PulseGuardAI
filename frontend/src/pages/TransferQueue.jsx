import React, { useState } from 'react';
import { 
  ArrowLeftRight, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  AlertCircle, 
  Search, 
  Filter,
  UserCheck,
  ShieldCheck
} from 'lucide-react';
import { Button, Badge, Input, Modal, ModalFooter } from '../components/ui';
import { TransferStepper } from '../components/transfer/TransferStepper';
import { useTransfer } from '../context/TransferContext';
import { useAuth } from '../context/AuthContext';

export const TransferQueue = () => {
  const { role } = useAuth();
  const { transfers, approveTransfer, rejectTransfer, toastMessage } = useTransfer();
  const [rejectModalOpen, setRejectModalOpen] = useState(false);
  const [selectedTransferId, setSelectedTransferId] = useState(null);
  const [rejectionReason, setRejectionReason] = useState('');
  const [filter, setFilter] = useState('all'); // 'all' | 'pending' | 'resolved'

  const handleOpenReject = (id) => {
    setSelectedTransferId(id);
    setRejectionReason('');
    setRejectModalOpen(true);
  };

  const handleConfirmReject = (e) => {
    e.preventDefault();
    if (!rejectionReason.trim()) return;
    rejectTransfer(selectedTransferId, rejectionReason.trim());
    setRejectModalOpen(false);
  };

  const filteredTransfers = transfers.filter(t => {
    if (filter === 'pending') return t.status === 'Pending';
    if (filter === 'resolved') return t.status === 'Approved' || t.status === 'Completed' || t.status === 'Rejected';
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Toast Banner */}
      {toastMessage && (
        <div className="fixed top-20 right-8 z-50 bg-slate-900 text-white px-4 py-3 rounded-2xl shadow-2xl border border-slate-700 flex items-center gap-3 animate-in slide-in-from-top-4">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
          <span className="text-xs font-semibold">{toastMessage}</span>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              Doctor-to-Doctor Transfer Queue
            </h1>
            <Badge variant="tier2" size="sm">
              {transfers.filter(t => t.status === 'Pending').length} Pending Review
            </Badge>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Admin Governance & Handover State Machine • Prevents split-brain physician assignments
          </p>
        </div>

        {/* Filter Pills */}
        <div className="flex bg-slate-100 p-1 rounded-xl">
          <button
            type="button"
            onClick={() => setFilter('all')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
              filter === 'all' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            All Transfers ({transfers.length})
          </button>
          <button
            type="button"
            onClick={() => setFilter('pending')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
              filter === 'pending' ? 'bg-amber-500 text-white shadow-xs' : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            Pending Only
          </button>
          <button
            type="button"
            onClick={() => setFilter('resolved')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
              filter === 'resolved' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            Resolved
          </button>
        </div>
      </div>

      {/* Transfers List */}
      <div className="space-y-4">
        {filteredTransfers.map(transfer => {
          const isPending = transfer.status === 'Pending';
          const isApproved = transfer.status === 'Approved' || transfer.status === 'Completed';
          const isRejected = transfer.status === 'Rejected';

          return (
            <div
              key={transfer.id}
              className={`p-6 rounded-2xl bg-white border transition-all duration-200 shadow-xs ${
                isPending ? 'border-amber-300 ring-2 ring-amber-100' : 'border-slate-200/80'
              }`}
            >
              <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-100">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-teal-50 border border-teal-200 flex items-center justify-center font-bold text-teal-800 shrink-0">
                    {transfer.bedId}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-bold text-sm text-slate-900">{transfer.patientName}</h3>
                      <Badge variant={transfer.priority === 'Urgent' ? 'tier2' : 'normal'} size="sm">
                        {transfer.priority}
                      </Badge>
                      <Badge 
                        variant={isApproved ? 'normal' : isRejected ? 'tier1' : 'tier2'} 
                        size="sm"
                        dot
                      >
                        {transfer.status}
                      </Badge>
                    </div>
                    <span className="text-xs text-slate-400 mt-0.5 block font-mono">
                      Request ID: {transfer.id} • {transfer.timestamp}
                    </span>
                  </div>
                </div>

                {/* Transfer Participants */}
                <div className="flex items-center gap-3 bg-slate-50 px-4 py-2 rounded-xl border border-slate-100 text-xs">
                  <div>
                    <span className="text-[10px] text-slate-400 uppercase font-semibold block">From</span>
                    <span className="font-bold text-slate-800">{transfer.fromDoctor}</span>
                  </div>
                  <ArrowLeftRight className="w-4 h-4 text-teal-600 shrink-0" />
                  <div>
                    <span className="text-[10px] text-slate-400 uppercase font-semibold block">To</span>
                    <span className="font-bold text-teal-800">{transfer.toDoctor}</span>
                  </div>
                </div>
              </div>

              {/* Clinical Rationale & Horizontal Stepper */}
              <div className="py-4 grid grid-cols-1 lg:grid-cols-2 gap-6 items-center">
                <div className="space-y-1.5">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                    Documented Clinical Rationale:
                  </span>
                  <p className="text-xs text-slate-700 bg-slate-50/70 p-3 rounded-xl border border-slate-100 leading-relaxed">
                    "{transfer.reason}"
                  </p>
                </div>

                <div className="bg-slate-50/50 p-2 rounded-xl">
                  <TransferStepper status={transfer.status} rejectionReason={transfer.rejectionReason} />
                </div>
              </div>

              {/* Action Area for Pending Transfers (Role-Isolated) */}
              {isPending && role === 'admin' && (
                <div className="pt-4 border-t border-slate-100 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-1.5 text-xs text-purple-700 font-semibold">
                    <ShieldCheck className="w-4 h-4" />
                    <span>Admin Clearance: Transfer Authorization Required</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <Button
                      variant="outline"
                      size="sm"
                      icon={XCircle}
                      onClick={() => handleOpenReject(transfer.id)}
                      className="text-red-600 hover:bg-red-50 border-red-200"
                    >
                      Reject Transfer
                    </Button>
                    <Button
                      variant="primary"
                      size="sm"
                      icon={CheckCircle2}
                      onClick={() => approveTransfer(transfer.id)}
                      className="bg-emerald-600 hover:bg-emerald-700 shadow-sm shadow-emerald-500/20"
                    >
                      Approve Transfer & Reassign Roster
                    </Button>
                  </div>
                </div>
              )}

              {isPending && role === 'doctor' && (
                <div className="pt-4 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className="text-amber-700 font-medium flex items-center gap-1.5">
                    <Clock className="w-4 h-4 text-amber-500" />
                    Awaiting Administrative Review & Bed Management Authorization
                  </span>
                  <Badge variant="tier2" size="sm">
                    Pending Admin Decision
                  </Badge>
                </div>
              )}
            </div>
          );
        })}

        {filteredTransfers.length === 0 && (
          <div className="text-center py-16 bg-white rounded-2xl border border-slate-200">
            <UserCheck className="w-10 h-10 text-slate-300 mx-auto mb-2" />
            <p className="text-sm font-semibold text-slate-700">No transfers currently in this queue</p>
            <p className="text-xs text-slate-400 mt-1">Pending requests submitted by attending doctors appear here</p>
          </div>
        )}
      </div>

      {/* Rejection Reason Modal */}
      <Modal
        isOpen={rejectModalOpen}
        onClose={() => setRejectModalOpen(false)}
        title="Reject Doctor Transfer Request"
        description="A clinical justification is required for rejecting patient handover"
      >
        <form onSubmit={handleConfirmReject} className="space-y-4">
          <Input
            label="Rejection Justification"
            placeholder="e.g. Unit at max capacity, subspecialty consult inappropriate..."
            value={rejectionReason}
            onChange={(e) => setRejectionReason(e.target.value)}
            helperText="Recorded to immutable audit ledger"
            required
          />

          <ModalFooter>
            <Button variant="ghost" onClick={() => setRejectModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="danger">
              Confirm Rejection
            </Button>
          </ModalFooter>
        </form>
      </Modal>
    </div>
  );
};

export default TransferQueue;
