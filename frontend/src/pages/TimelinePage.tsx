import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { timelineService } from '../services/timeline';
import { usePatient } from '../hooks/usePatient';
import { TimelineEvent } from '../components/TimelineEvent';
import { Button } from '../components/ui/Button';
import { ArrowDownUp, Filter } from 'lucide-react';
import { Skeleton } from '../components/ui/Skeleton';
import { ErrorState } from '../components/ErrorState';
import { EmptyState } from '../components/EmptyState';

export const TimelinePage: React.FC = () => {
  const { selectedPatientId } = usePatient();
  const [order, setOrder] = useState<'desc' | 'asc'>('desc');

  const { data, isLoading, error } = useQuery({
    queryKey: ['timeline', selectedPatientId],
    queryFn: () => timelineService.getTimeline(selectedPatientId!),
    enabled: !!selectedPatientId,
  });

  if (!selectedPatientId) return <div>Select a patient</div>;
  if (isLoading) return <div className="space-y-8 p-6"><Skeleton className="h-24 w-full" /><Skeleton className="h-24 w-full" /></div>;
  if (error || !data) return <ErrorState error={error} />;
  if (data.length === 0) return <EmptyState title="No timeline events" description="Upload documents to generate a timeline." />;

  const displayData = order === 'desc' ? [...data] : [...data].reverse();

  return (
    <div className="max-w-4xl mx-auto py-6">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">Patient Timeline</h2>
          <p className="text-slate-500 mt-1">Chronological view of extracted medical events.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => setOrder(order === 'desc' ? 'asc' : 'desc')}>
            <ArrowDownUp className="w-4 h-4 mr-2" />
            {order === 'desc' ? 'Newest First' : 'Oldest First'}
          </Button>
          <Button variant="outline" size="sm">
            <Filter className="w-4 h-4 mr-2" />
            Filter
          </Button>
        </div>
      </div>

      <div className="space-y-12">
        {displayData.map((entry) => (
          <div key={entry.date}>
            <div className="sticky top-0 z-10 bg-slate-50/90 backdrop-blur py-2 mb-4">
              <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider">{entry.date}</h3>
            </div>
            <div className="space-y-6">
              {entry.events.map((event) => (
                <TimelineEvent key={event.id} event={event} />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
