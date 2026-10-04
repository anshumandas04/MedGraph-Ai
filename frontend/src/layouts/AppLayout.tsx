import React, { useState } from 'react';
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { usePatient } from '../hooks/usePatient';
import { PrototypeNotice } from '../components/PrototypeNotice';
import { 
  LayoutDashboard, Clock, Share2, FileText, Activity, 
  Pill, FlaskConical, Search, BarChart3, Settings, LogOut, ScrollText
} from 'lucide-react';

interface PatientProfileSetupProps {
  fullName: string;
  onSubmit: (data: {
    first_name: string;
    last_name: string;
    date_of_birth: string;
    gender: string;
  }) => Promise<void>;
}

const PatientProfileSetup: React.FC<PatientProfileSetupProps> = ({ fullName, onSubmit }) => {
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const nameParts = fullName.trim().split(/\s+/);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    setIsSubmitting(true);
    const form = new FormData(event.currentTarget);
    try {
      await onSubmit({
        first_name: String(form.get('first_name') ?? '').trim(),
        last_name: String(form.get('last_name') ?? '').trim(),
        date_of_birth: String(form.get('date_of_birth') ?? ''),
        gender: String(form.get('gender') ?? ''),
      });
    } catch {
      setError('We could not create your patient profile. Check the details and try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="max-w-xl rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-xl font-semibold text-slate-900">Set up your health record</h2>
      <p className="mt-2 text-sm text-slate-600">Add the details needed to link this account to your own patient record. Your account will not be able to select another patient.</p>
      {error && <p role="alert" className="mt-4 rounded bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      <form onSubmit={handleSubmit} className="mt-5 space-y-4">
        <div>
          <label htmlFor="profile-first-name" className="mb-1 block text-sm font-medium text-slate-700">First name</label>
          <input id="profile-first-name" name="first_name" required maxLength={100} defaultValue={nameParts[0] ?? ''} className="w-full rounded-md border border-slate-300 px-3 py-2" />
        </div>
        <div>
          <label htmlFor="profile-last-name" className="mb-1 block text-sm font-medium text-slate-700">Last name</label>
          <input id="profile-last-name" name="last_name" required maxLength={100} defaultValue={nameParts.slice(1).join(' ')} className="w-full rounded-md border border-slate-300 px-3 py-2" />
        </div>
        <div>
          <label htmlFor="profile-date-of-birth" className="mb-1 block text-sm font-medium text-slate-700">Date of birth</label>
          <input id="profile-date-of-birth" name="date_of_birth" type="date" required max={new Date().toISOString().slice(0, 10)} className="w-full rounded-md border border-slate-300 px-3 py-2" />
        </div>
        <div>
          <label htmlFor="profile-gender" className="mb-1 block text-sm font-medium text-slate-700">Gender</label>
          <select id="profile-gender" name="gender" required defaultValue="Prefer not to say" className="w-full rounded-md border border-slate-300 px-3 py-2">
            <option>Prefer not to say</option>
            <option>Female</option>
            <option>Male</option>
            <option>Non-binary</option>
            <option>Another identity</option>
          </select>
        </div>
        <button type="submit" disabled={isSubmitting} className="rounded-md bg-primary-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-60">
          {isSubmitting ? 'Saving…' : 'Create my record'}
        </button>
      </form>
    </section>
  );
};

export const AppLayout: React.FC = () => {
  const { user, logout } = useAuth();
  const {
    availablePatients,
    selectedPatientId,
    selectedPatient,
    selectPatient,
    createMyProfile,
    needsProfile,
    loadError,
    isLoading: isPatientLoading,
  } = usePatient();
  const navigate = useNavigate();
  const location = useLocation();
  const canSelectPatient = user?.role === 'ADMIN' || user?.role === 'CLINICIAN';

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { to: "/app/dashboard", icon: <LayoutDashboard className="w-5 h-5" />, label: "Overview" },
    { to: "/app/timeline", icon: <Clock className="w-5 h-5" />, label: "Timeline" },
    { to: "/app/graph", icon: <Share2 className="w-5 h-5" />, label: "Knowledge Graph" },
    { to: "/app/documents", icon: <FileText className="w-5 h-5" />, label: "Documents" },
    { to: "/app/signals", icon: <Activity className="w-5 h-5" />, label: "Signals" },
    { to: "/app/medications", icon: <Pill className="w-5 h-5" />, label: "Medications" },
    { to: "/app/investigations", icon: <FlaskConical className="w-5 h-5" />, label: "Investigations" },
    { to: "/app/ask", icon: <Search className="w-5 h-5" />, label: "Ask MedGraph" },
  ];

  if (user?.role === 'ADMIN') {
    navItems.push({ to: "/app/research", icon: <BarChart3 className="w-5 h-5" />, label: "Research Dashboard" });
    navItems.push({ to: "/app/diagnostics", icon: <ScrollText className="w-5 h-5" />, label: "System Diagnostics" });
  }
  const isAdminDiagnostics = user?.role === 'ADMIN' && location.pathname === '/app/diagnostics';

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <PrototypeNotice />
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col">
          <div className="p-4 border-b border-slate-800">
            <h1 className="text-xl font-bold text-white tracking-tight">MedGraph</h1>
            <p className="text-xs text-slate-500 mt-1">Research Prototype v0.1</p>
          </div>
          <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) => 
                  `flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive 
                      ? 'bg-primary-600 text-white' 
                      : 'hover:bg-slate-800 hover:text-white'
                  }`
                }
              >
                {item.icon}
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="p-4 border-t border-slate-800 space-y-1">
            <NavLink 
              to="/app/settings" 
              className={({isActive}) => `flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive ? 'bg-slate-800 text-white' : 'hover:bg-slate-800 hover:text-white'}`}
            >
              <Settings className="w-5 h-5" />
              Settings
            </NavLink>
            <button 
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium hover:bg-slate-800 hover:text-white transition-colors"
            >
              <LogOut className="w-5 h-5" />
              Logout
            </button>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 flex flex-col h-full overflow-hidden">
          <header className="bg-white border-b border-slate-200 px-6 py-4 flex justify-between items-center shrink-0">
            <div>
              {canSelectPatient ? (
                <label className="flex items-center gap-3 text-sm text-slate-600">
                  <span>Patient</span>
                  <select
                    aria-label="Select patient"
                    value={selectedPatientId ?? ''}
                    onChange={(event) => selectPatient(event.target.value)}
                    disabled={isPatientLoading || availablePatients.length === 0}
                    className="min-w-56 rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-900 disabled:bg-slate-100"
                  >
                    {availablePatients.length === 0 && <option value="">{isPatientLoading ? 'Loading patients…' : 'No patients available'}</option>}
                    {availablePatients.map((patient) => (
                      <option key={patient.id} value={patient.id}>{patient.first_name} {patient.last_name}</option>
                    ))}
                  </select>
                </label>
              ) : user?.role === 'PATIENT' ? (
                <span className="text-sm text-slate-600">
                  {selectedPatient ? `My record: ${selectedPatient.first_name} ${selectedPatient.last_name}` : 'My health record'}
                </span>
              ) : null}
            </div>
            <div className="flex items-center gap-3 text-sm">
              <span className="text-slate-500">Logged in as</span>
              <span className="font-medium text-slate-900">{user?.full_name}</span>
              <span className="bg-slate-100 px-2 py-0.5 rounded text-xs text-slate-600">{user?.role}</span>
            </div>
          </header>
          <div className="flex-1 overflow-y-auto p-6">
            {isAdminDiagnostics ? (
              <Outlet />
            ) : isPatientLoading ? (
              <p className="text-sm text-slate-500">Loading your patient access…</p>
            ) : loadError ? (
              <div role="alert" className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">{loadError}</div>
            ) : needsProfile ? (
              <PatientProfileSetup fullName={user?.full_name ?? ''} onSubmit={createMyProfile} />
            ) : !selectedPatientId ? (
              <div className="rounded-md border border-slate-200 bg-white p-6 text-sm text-slate-600">
                No patient records are assigned to this account. Ask an administrator to create or assign a patient record.
              </div>
            ) : (
              <Outlet />
            )}
          </div>
        </main>
      </div>
    </div>
  );
};
