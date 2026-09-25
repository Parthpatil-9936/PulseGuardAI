import React, { useState } from 'react';
import { 
  FileText, 
  MessageSquare, 
  ShieldAlert, 
  CheckCircle2, 
  ArrowLeftRight, 
  Edit3, 
  Plus, 
  Save, 
  X,
  Stethoscope,
  Activity,
  Clock
} from 'lucide-react';
import { Button, Badge, Input } from '../ui';
import { useAuth } from '../../context/AuthContext';

export const ClinicalNotesTimeline = ({ bedId, patientName }) => {
  const { user, role } = useAuth();
  const [filter, setFilter] = useState('all'); // 'all' | 'notes' | 'alerts' | 'transfers'
  const [editingNoteId, setEditingNoteId] = useState(null);
  const [editedContent, setEditedContent] = useState('');
  const [isAddingNote, setIsAddingNote] = useState(false);
  const [newNoteText, setNewNoteText] = useState('');

  // Initial timeline feed
  const [timelineEvents, setTimelineEvents] = useState([
    {
      id: 'evt_1',
      type: 'alert',
      tier: 'tier1',
      title: 'Tier 1 Critical Alarm Triggered',
      details: 'Deterministic Hard Threshold breached: SpO2 dropped to 81%, HR accelerated to 138 BPM.',
      author: 'Edge Sensor Triage Engine',
      timestamp: '10:42 AM',
      icon: ShieldAlert,
    },
    {
      id: 'evt_2',
      type: 'ack',
      title: 'Alert Acknowledged at Bedside',
      details: 'Clinician confirmed telemetry alarm. Supplemental high-flow oxygen (15L Non-Rebreather) initiated.',
      author: 'Dr. Sarah Chen, MD',
      role: 'doctor',
      timestamp: '10:44 AM',
      icon: CheckCircle2,
    },
    {
      id: 'evt_3',
      type: 'doctor-note',
      title: 'Attending Physician Assessment',
      details: 'Patient exhibiting acute respiratory fatigue secondary to septic pulmonary edema. Arterial blood gas ordered. Titrating IV vasopressors.',
      author: 'Dr. Sarah Chen, MD',
      role: 'doctor',
      timestamp: '09:15 AM',
      editable: true,
      icon: Stethoscope,
    },
    {
      id: 'evt_4',
      type: 'doctor-note',
      title: 'Pulmonary Specialist Consultation',
      details: 'Bilateral lung crackles audible at lung bases. Patient reports mild dyspnea, alert and oriented x3. Vasopressor titration holding MAP > 65.',
      author: 'Dr. Marcus Vance, MD',
      role: 'doctor',
      timestamp: '08:30 AM',
      editable: true,
      icon: Stethoscope,
    },
    {
      id: 'evt_5',
      type: 'transfer',
      title: 'Primary Physician Assignment Handover',
      details: 'Transferred from Dr. Marcus Vance to Dr. Sarah Chen for specialized coronary intensive care.',
      author: 'System Audit Ledger',
      timestamp: '07:00 AM',
      icon: ArrowLeftRight,
    }
  ]);

  const handleStartEdit = (evt) => {
    setEditingNoteId(evt.id);
    setEditedContent(evt.details);
  };

  const handleSaveEdit = (id) => {
    setTimelineEvents(prev => prev.map(evt => {
      if (evt.id === id) {
        return {
          ...evt,
          details: editedContent,
          edited: true,
          editedAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
      }
      return evt;
    }));
    setEditingNoteId(null);
  };

  const handleAddNote = (e) => {
    e.preventDefault();
    if (!newNoteText.trim()) return;

    const newEvt = {
      id: `evt_${Date.now()}`,
      type: 'doctor-note',
      title: 'Physician Progress Note',
      details: newNoteText.trim(),
      author: user?.name || 'Attending Physician',
      role: 'doctor',
      timestamp: 'Just now',
      editable: true,
      icon: Stethoscope,
    };

    setTimelineEvents([newEvt, ...timelineEvents]);
    setNewNoteText('');
    setIsAddingNote(false);
  };

  const filteredEvents = timelineEvents.filter(evt => {
    if (filter === 'notes') return evt.type === 'doctor-note';
    if (filter === 'alerts') return evt.type === 'alert' || evt.type === 'ack';
    if (filter === 'transfers') return evt.type === 'transfer';
    return true;
  });

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-5 space-y-4">
      {/* Header & Filter Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-[#0EA5B7]" />
          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
            Clinical Notes & Audit Timeline
          </h3>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex bg-slate-100 p-0.5 rounded-xl">
            {['all', 'notes', 'alerts', 'transfers'].map(f => (
              <button
                key={f}
                type="button"
                onClick={() => setFilter(f)}
                className={`px-2.5 py-1 text-[11px] font-semibold rounded-lg capitalize transition-colors ${
                  filter === f ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                {f}
              </button>
            ))}
          </div>

          <Button
            variant="primary"
            size="sm"
            icon={Plus}
            onClick={() => setIsAddingNote(!isAddingNote)}
          >
            Add Clinical Note
          </Button>
        </div>
      </div>

      {/* Inline Add Note Form */}
      {isAddingNote && (
        <form onSubmit={handleAddNote} className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-800">
              Record Physician Note
            </span>
            <Badge variant="doctor" size="sm">
              Clinical Note
            </Badge>
          </div>

          <textarea
            rows="3"
            value={newNoteText}
            onChange={(e) => setNewNoteText(e.target.value)}
            placeholder="Enter physician clinical rationale, assessment, or plan..."
            className="w-full text-xs p-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 bg-white"
            required
          />

          <div className="flex justify-end gap-2">
            <Button variant="ghost" size="sm" onClick={() => setIsAddingNote(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm">
              Save Entry to Ledger
            </Button>
          </div>
        </form>
      )}

      {/* Chronological Timeline Feed */}
      <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
        {filteredEvents.map(evt => {
          const Icon = evt.icon;
          const isEditing = editingNoteId === evt.id;

          let badgeVariant = 'normal';
          let borderAccent = 'border-slate-200';
          let iconBg = 'bg-teal-50 text-[#0D8A9A]';

          if (evt.type === 'alert') {
            badgeVariant = evt.tier || 'tier1';
            borderAccent = 'border-red-200 bg-red-50/20';
            iconBg = 'bg-red-100 text-red-700';
          } else if (evt.type === 'transfer') {
            badgeVariant = 'tier2';
            iconBg = 'bg-amber-100 text-amber-700';
          }

          return (
            <div key={evt.id} className="relative group">
              {/* Timeline dot/icon */}
              <div className={`absolute -left-6 top-1.5 w-6 h-6 rounded-full border-2 border-white shadow-xs flex items-center justify-center shrink-0 ${iconBg}`}>
                <Icon className="w-3 h-3" />
              </div>

              {/* Event Card */}
              <div className={`p-4 rounded-xl border ${borderAccent} bg-white shadow-xs space-y-1.5`}>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-900">{evt.title}</span>
                    {evt.type === 'doctor-note' && (
                      <Badge variant="doctor" size="sm">Physician</Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-[11px] text-slate-400">
                    <Clock className="w-3 h-3" />
                    <span>{evt.timestamp}</span>
                    <span>• {evt.author}</span>
                  </div>
                </div>

                {/* Details Content or Inline Editing */}
                {isEditing ? (
                  <div className="space-y-2 pt-1">
                    <textarea
                      rows="2"
                      value={editedContent}
                      onChange={(e) => setEditedContent(e.target.value)}
                      className="w-full text-xs p-2 rounded-lg border border-teal-400 focus:outline-none focus:ring-1 focus:ring-teal-500 bg-teal-50/20"
                    />
                    <div className="flex justify-end gap-2">
                      <Button variant="ghost" size="sm" onClick={() => setEditingNoteId(null)}>
                        Cancel
                      </Button>
                      <Button variant="primary" size="sm" icon={Save} onClick={() => handleSaveEdit(evt.id)}>
                        Save Update
                      </Button>
                    </div>
                  </div>
                ) : (
                  <p className="text-xs text-slate-600 leading-relaxed">
                    {evt.details}
                    {evt.edited && (
                      <span className="text-[10px] text-slate-400 italic ml-2">
                        (edited at {evt.editedAt})
                      </span>
                    )}
                  </p>
                )}

                {/* Inline Edit Button (for doctor notes when logged in as Doctor) */}
                {!isEditing && evt.editable && role === 'doctor' && (
                  <div className="pt-1 flex justify-end">
                    <button
                      type="button"
                      onClick={() => handleStartEdit(evt)}
                      className="text-[11px] text-slate-400 hover:text-[#0EA5B7] flex items-center gap-1 transition-colors"
                    >
                      <Edit3 className="w-3 h-3" />
                      <span>Edit Note</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ClinicalNotesTimeline;
