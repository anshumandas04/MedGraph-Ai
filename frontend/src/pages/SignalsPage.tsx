import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { signalsService } from '../services/signals';
import { usePatient } from '../hooks/usePatient';
import { SignalCard } from '../components/SignalCard';
import { Tabs } from '../components/ui/Tabs';
import { Skeleton } from '../components/ui/Skeleton';
import { ErrorState } from '../components/ErrorState';

export const SignalsPage: React.FC = () => {
  const { selectedPatientId } = usePatient();

  const { data, isLoading, error } = useQuery({
    queryKey: ['signals', selectedPatientId],
    queryFn: () => signalsService.getSignals(selectedPatientId!),
    enabled: !!selectedPatientId,
  });

  if (!selectedPatientId) return <div>Select a patient</div>;
  if (isLoading) return <div className="space-y-4 p-6"><Skeleton className="h-32 w-full" /></div>;
  if (error || !data) return <ErrorState />;

  const openSignals = data.filter(s => s.status === 'OPEN' || s.status === 'NEEDS_VERIFICATION');
  const verifiedSignals = data.filter(s => s.status === 'VERIFIED');
  const dismissedSignals = data.filter(s => s.status === 'DISMISSED');

  const renderSignalList = (signals: typeof data) => (
    <div className="space-y-4 mt-4">
      {signals.map(signal => (
        <SignalCard key={signal.id} signal={signal} />
      ))}
      {signals.length === 0 && <div className="p-8 text-center text-slate-500">No signals found.</div>}
    </div>
  );

  const tabs = [
    { id: 'open', label: `Needs Review (${openSignals.length})`, content: renderSignalList(openSignals) },
    { id: 'verified', label: `Verified (${verifiedSignals.length})`, content: renderSignalList(verifiedSignals) },
    { id: 'dismissed', label: `Dismissed (${dismissedSignals.length})`, content: renderSignalList(dismissedSignals) },
    { id: 'all', label: `All (${data.length})`, content: renderSignalList(data) },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">Clinical Signals</h2>
        <p className="text-slate-500 mt-1">AI-generated alerts for conflicting information or missing follow-ups.</p>
      </div>

      <Tabs tabs={tabs} />
    </div>
  );
};
