import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { dashboardService } from '../services/dashboard';
import { usePatient } from '../hooks/usePatient';
import { StatCard } from '../components/StatCard';
import { SignalCard } from '../components/SignalCard';
import { FileText, Activity, Pill, AlertTriangle } from 'lucide-react';
import { Skeleton } from '../components/ui/Skeleton';
import { ErrorState } from '../components/ErrorState';
import { Link } from 'react-router-dom';
import { Badge } from '../components/ui/Badge';

export const DashboardPage: React.FC = () => {
  const { selectedPatientId } = usePatient();

  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard', selectedPatientId],
    queryFn: () => dashboardService.getDashboard(selectedPatientId!),
    enabled: !!selectedPatientId,
  });

  if (!selectedPatientId) return <div className="p-8">Please select a patient.</div>;
  if (isLoading) return <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 p-6"><Skeleton className="h-32" /><Skeleton className="h-32" /></div>;
  if (error || !data) return <ErrorState error={error} />;

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">Dashboard</h2>
        <p className="text-slate-500 mt-1">Overview of the patient's medical history.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="Documents" value={data.total_documents} icon={<FileText />} />
        <StatCard title="Health Events" value={data.total_events} icon={<Activity />} />
        <StatCard title="Active Signals" value={data.open_signals} icon={<AlertTriangle className="text-amber-500" />} />
        <StatCard title="Medications" value={data.total_medications} icon={<Pill />} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-slate-900">Recent Signals</h3>
            <Link to="/app/signals" className="text-sm font-medium text-primary-600 hover:underline">View all</Link>
          </div>
          <div className="space-y-4">
            {data.recent_signals.map(signal => (
              <SignalCard key={signal.id} signal={signal} />
            ))}
            {data.recent_signals.length === 0 && (
              <div className="p-8 text-center text-slate-500 bg-white rounded-lg border border-slate-200">No active signals.</div>
            )}
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-slate-900">Recent Documents</h3>
            <Link to="/app/documents" className="text-sm font-medium text-primary-600 hover:underline">View all</Link>
          </div>
          <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
            <ul className="divide-y divide-slate-200">
              {data.recent_documents.map(doc => (
                <li key={doc.id} className="p-4 hover:bg-slate-50">
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="font-medium text-slate-900">{doc.original_filename}</p>
                      <p className="text-sm text-slate-500">{doc.document_type} • {doc.document_date}</p>
                    </div>
                    <Badge variant={doc.processing_status === 'COMPLETED' ? 'success' : 'warning'}>
                      {doc.processing_status}
                    </Badge>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
