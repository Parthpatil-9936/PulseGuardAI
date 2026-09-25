import React, { useState } from 'react';
import { 
  Users, 
  UserPlus, 
  Shield, 
  CheckCircle2, 
  XCircle, 
  Search, 
  Filter, 
  Edit2, 
  Trash2, 
  Mail,
  Stethoscope,
  Activity
} from 'lucide-react';
import { Button, Badge, Avatar, Input, Select, Modal, ModalFooter } from '../../components/ui';

export const UserManagement = () => {
  const [users, setUsers] = useState([
    {
      id: 'usr_01',
      name: 'Dr. Sarah Chen, MD',
      email: 'dr.chen@pulseguard.icu',
      role: 'doctor',
      department: 'Critical Care / Cardiology',
      assignedBeds: ['Bed 01', 'Bed 02', 'Bed 04', 'Bed 07', 'Bed 10'],
      status: 'active',
      lastActive: 'Just now',
    },
    {
      id: 'usr_02',
      name: 'Dr. Marcus Vance, MD',
      email: 'dr.vance@pulseguard.icu',
      role: 'doctor',
      department: 'ICU Directorship',
      assignedBeds: ['Bed 03', 'Bed 05', 'Bed 09'],
      status: 'active',
      lastActive: '12m ago',
    },
    {
      id: 'usr_03',
      name: 'Dr. Elena Rostova, MD',
      email: 'dr.rostova@pulseguard.icu',
      role: 'doctor',
      department: 'Pulmonology / Critical Care',
      assignedBeds: ['Bed 06', 'Bed 08'],
      status: 'active',
      lastActive: '1h ago',
    },
    {
      id: 'usr_04',
      name: 'Priya Patel, RN',
      email: 'priya.rn@pulseguard.icu',
      role: 'nurse',
      department: 'Ward 4 Floor Nursing',
      assignedBeds: ['All Beds (01-10)'],
      status: 'active',
      lastActive: '2m ago',
    },
    {
      id: 'usr_05',
      name: 'David Kim, RN',
      email: 'david.kim@pulseguard.icu',
      role: 'nurse',
      department: 'Ward 4 Floor Nursing',
      assignedBeds: ['Beds 01-05'],
      status: 'active',
      lastActive: '30m ago',
    },
    {
      id: 'usr_06',
      name: 'Alex Rivera',
      email: 'admin.rivera@pulseguard.icu',
      role: 'admin',
      department: 'Biomedical Informatics',
      assignedBeds: ['System Scope'],
      status: 'active',
      lastActive: 'Now',
    }
  ]);

  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [newName, setNewName] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [newRole, setNewRole] = useState('doctor');
  const [newDept, setNewDept] = useState('Critical Care Unit');

  const toggleUserStatus = (id) => {
    setUsers(prev => prev.map(u => {
      if (u.id === id) {
        return {
          ...u,
          status: u.status === 'active' ? 'inactive' : 'active'
        };
      }
      return u;
    }));
  };

  const handleAddUser = (e) => {
    e.preventDefault();
    if (!newName.trim() || !newEmail.trim()) return;

    const newUser = {
      id: `usr_${Date.now()}`,
      name: newName.trim(),
      email: newEmail.trim(),
      role: newRole,
      department: newDept,
      assignedBeds: newRole === 'nurse' ? ['Ward Float'] : ['Unassigned'],
      status: 'active',
      lastActive: 'Registered',
    };

    setUsers([...users, newUser]);
    setIsAddModalOpen(false);
    setNewName('');
    setNewEmail('');
  };

  const filteredUsers = users.filter(u => {
    if (roleFilter !== 'all' && u.role !== roleFilter) return false;
    if (search.trim()) {
      const q = search.toLowerCase();
      return u.name.toLowerCase().includes(q) || u.email.toLowerCase().includes(q) || u.department.toLowerCase().includes(q);
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              Clinician & Staff Directory
            </h1>
            <Badge variant="admin" size="sm">
              Admin Governance
            </Badge>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Role-Based Access Control (RBAC) • Patient assignments & clinical authorization
          </p>
        </div>

        <Button
          variant="primary"
          size="sm"
          icon={UserPlus}
          onClick={() => setIsAddModalOpen(true)}
        >
          Provision Staff Account
        </Button>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-white p-4 rounded-2xl border border-slate-200/80">
        <div className="w-full sm:w-72">
          <Input
            placeholder="Search by name, email, department..."
            icon={Search}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="py-1.5 text-xs"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          {['all', 'doctor', 'nurse', 'admin'].map(r => (
            <button
              key={r}
              type="button"
              onClick={() => setRoleFilter(r)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-xl capitalize transition-colors ${
                roleFilter === r
                  ? 'bg-slate-900 text-white shadow-xs'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {r}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-3.5 px-4">Clinician / Staff</th>
                <th className="py-3.5 px-4">Role</th>
                <th className="py-3.5 px-4">Department</th>
                <th className="py-3.5 px-4">Assigned Beds</th>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4">Last Activity</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {filteredUsers.map(u => (
                <tr key={u.id} className="hover:bg-slate-50/70 transition-colors">
                  <td className="py-3.5 px-4">
                    <div className="flex items-center gap-3">
                      <Avatar name={u.name} role={u.role} size="md" status={u.status === 'active' ? 'online' : 'offline'} />
                      <div>
                        <span className="font-bold text-slate-900 block leading-tight">{u.name}</span>
                        <span className="text-[11px] text-slate-400 font-mono">{u.email}</span>
                      </div>
                    </div>
                  </td>
                  <td className="py-3.5 px-4">
                    <Badge variant={u.role} size="sm">
                      {u.role.toUpperCase()}
                    </Badge>
                  </td>
                  <td className="py-3.5 px-4 font-medium text-slate-600">
                    {u.department}
                  </td>
                  <td className="py-3.5 px-4">
                    <div className="flex flex-wrap gap-1 max-w-xs">
                      {u.assignedBeds.map((bed, idx) => (
                        <span key={idx} className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded text-[11px] font-mono">
                          {bed}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="py-3.5 px-4">
                    <button
                      type="button"
                      onClick={() => toggleUserStatus(u.id)}
                      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold transition-colors ${
                        u.status === 'active'
                          ? 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200'
                          : 'bg-slate-100 text-slate-500 hover:bg-slate-200'
                      }`}
                    >
                      <span className={`w-1.5 h-1.5 rounded-full ${u.status === 'active' ? 'bg-emerald-500' : 'bg-slate-400'}`} />
                      <span>{u.status === 'active' ? 'Active' : 'Suspended'}</span>
                    </button>
                  </td>
                  <td className="py-3.5 px-4 font-mono text-[11px] text-slate-400">
                    {u.lastActive}
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => toggleUserStatus(u.id)}
                      className="text-slate-400 hover:text-slate-800"
                    >
                      Toggle
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Clinician Modal */}
      <Modal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title="Provision Clinician Staff Account"
        description="Issue clinical credentials with cryptographic key allocation"
      >
        <form onSubmit={handleAddUser} className="space-y-4">
          <Input
            label="Full Clinician Name"
            placeholder="e.g. Dr. Julian Croft, MD"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            required
          />

          <Input
            label="Staff Email Address"
            type="email"
            placeholder="e.g. j.croft@pulseguard.icu"
            value={newEmail}
            onChange={(e) => setNewEmail(e.target.value)}
            required
          />

          <Select
            label="Assigned Clinical Role"
            value={newRole}
            onChange={(e) => setNewRole(e.target.value)}
            options={[
              { value: 'doctor', label: 'Doctor (Attending / Fellow)' },
              { value: 'nurse', label: 'Nurse (Staff / Critical Care RN)' },
              { value: 'admin', label: 'Admin (Clinical Systems)' },
            ]}
          />

          <Input
            label="Department / Unit"
            value={newDept}
            onChange={(e) => setNewDept(e.target.value)}
            required
          />

          <ModalFooter>
            <Button variant="ghost" onClick={() => setIsAddModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary">
              Provision Credentials
            </Button>
          </ModalFooter>
        </form>
      </Modal>
    </div>
  );
};

export default UserManagement;
