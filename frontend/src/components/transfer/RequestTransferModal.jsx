import React, { useState } from 'react';
import { ArrowLeftRight, User, Stethoscope, AlertTriangle } from 'lucide-react';
import { Modal, ModalFooter, Button, Input, Select } from '../ui';
import { useAuth } from '../../context/AuthContext';
import { useTransfer } from '../../context/TransferContext';

export const RequestTransferModal = ({
  isOpen,
  onClose,
  patient,
}) => {
  const { user } = useAuth();
  const { requestTransfer } = useTransfer();

  const [toDoctor, setToDoctor] = useState('Dr. Marcus Vance, MD');
  const [reason, setReason] = useState('');
  const [priority, setPriority] = useState('Routine');
  const [submitting, setSubmitting] = useState(false);

  if (!patient) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!reason.trim()) return;

    setSubmitting(true);
    setTimeout(() => {
      requestTransfer({
        patientName: patient.patientName,
        bedId: patient.bedId,
        fromDoctor: user.name,
        toDoctor,
        reason: reason.trim(),
        priority,
      });
      setSubmitting(false);
      onClose();
      setReason('');
    }, 400);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Request Doctor Patient Transfer"
      description={`Patient: ${patient.patientName} • Bed ${patient.bedId}`}
      size="md"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Current State Info */}
        <div className="p-3 bg-teal-50/70 border border-teal-200/80 rounded-xl flex items-center justify-between text-xs">
          <div>
            <span className="text-[10px] text-teal-700 font-semibold uppercase block">Current Attending</span>
            <span className="font-bold text-teal-950">{user.name}</span>
          </div>
          <ArrowLeftRight className="w-4 h-4 text-teal-600" />
          <div className="text-right">
            <span className="text-[10px] text-teal-700 font-semibold uppercase block">Target Specialty</span>
            <span className="font-bold text-teal-950">Critical Care Review</span>
          </div>
        </div>

        {/* Destination Doctor Select */}
        <Select
          label="Transfer Destination Doctor"
          value={toDoctor}
          onChange={(e) => setToDoctor(e.target.value)}
          options={[
            { value: 'Dr. Marcus Vance, MD', label: 'Dr. Marcus Vance, MD (ICU Director)' },
            { value: 'Dr. Elena Rostova, MD', label: 'Dr. Elena Rostova, MD (Pulmonology / Critical Care)' },
            { value: 'Dr. Sarah Chen, MD', label: 'Dr. Sarah Chen, MD (Cardiology Attending)' },
          ]}
          required
        />

        {/* Priority */}
        <Select
          label="Transfer Urgency Priority"
          value={priority}
          onChange={(e) => setPriority(e.target.value)}
          options={[
            { value: 'Routine', label: 'Routine (Scheduled shift / unit handover)' },
            { value: 'Urgent', label: 'Urgent (Clinical step-up / deterioration trend)' },
            { value: 'STAT', label: 'STAT (Immediate bedside intervention required)' },
          ]}
        />

        {/* Clinical Rationale */}
        <div className="space-y-1.5">
          <label className="block text-xs font-semibold text-slate-700">
            Clinical Rationale / Reason <span className="text-red-500">*</span>
          </label>
          <textarea
            rows="3"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Document patient acuity, rationale for transfer, and current treatment status..."
            className="w-full text-xs p-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 bg-white"
            required
          />
        </div>

        <ModalFooter>
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            loading={submitting}
            icon={ArrowLeftRight}
          >
            Submit Transfer Request
          </Button>
        </ModalFooter>
      </form>
    </Modal>
  );
};

export default RequestTransferModal;
