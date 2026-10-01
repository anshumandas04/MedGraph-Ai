import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { medicationsService } from '../services/medications';
import { usePatient } from '../hooks/usePatient';
import { Badge } from '../components/ui/Badge';
import { Card, CardContent } from '../components/ui/Card';
import { Skeleton } from '../components/ui/Skeleton';
import { ErrorState } from '../components/ErrorState';
import { Pill } from 'lucide-react';

export const MedicationsPage: React.FC = () => {
  const { selectedPatientId } = usePatient();

  const { data, isLoading, error } = useQuery({
    queryKey: ['medications', selectedPatientId],
    queryFn: () => medicationsService.getMedications(selectedPatientId!),
    enabled: !!selectedPatientId,
  });

  if (!selectedPatientId) return <div>Select a patient</div>;
  if (isLoading) return <div className="space-y-4 p-6"><Skeleton className="h-24 w-full" /></div>;
  if (error || !data) return <ErrorState />;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">Medications</h2>
        <p className="text-slate-500 mt-1">Extracted medication history and current status.</p>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {data.map(med => (
          <Card key={med.id}>
            <CardContent className="p-4 sm:p-6 flex flex-col sm:flex-row gap-6">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <div className="bg-primary-100 p-2 rounded-full text-primary-600">
                    <Pill className="w-5 h-5" />
                  </div>
                  <h3 className="text-lg font-semibold text-slate-900">{med.name}</h3>
                  <Badge variant={med.status === 'ACTIVE' ? 'success' : 'default'}>{med.status}</Badge>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4 text-sm">
                  <div>
                    <span className="block text-slate-500 mb-1">Dosage</span>
                    <span className="font-medium text-slate-900">{med.dosage || '-'}</span>
                  </div>
                  <div>
                    <span className="block text-slate-500 mb-1">Frequency</span>
                    <span className="font-medium text-slate-900">{med.frequency || '-'}</span>
                  </div>
                  <div>
                    <span className="block text-slate-500 mb-1">Route</span>
                    <span className="font-medium text-slate-900">{med.route || '-'}</span>
                  </div>
                  <div>
                    <span className="block text-slate-500 mb-1">Duration</span>
                    <span className="font-medium text-slate-900">
                      {med.start_date || '?'} to {med.end_date || 'Present'}
                    </span>
                  </div>
                </div>
              </div>
              
              <div className="w-full sm:w-64 border-t sm:border-t-0 sm:border-l border-slate-200 pt-4 sm:pt-0 sm:pl-6">
                <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">History</h4>
                <div className="space-y-3">
                  {med.events.map((ev, i) => (
                    <div key={i} className="text-sm">
                      <div className="font-medium text-slate-900">{ev.action}</div>
                      <div className="text-slate-500 text-xs">{ev.date}</div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};
