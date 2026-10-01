import React from 'react';
import { HealthEvent } from '../types';
import { Card, CardHeader, CardTitle, CardContent } from './ui/Card';
import { Badge } from './ui/Badge';
import { EvidenceItem } from './EvidenceItem';

export const EventCard: React.FC<{ event: HealthEvent }> = ({ event }) => {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex justify-between items-start">
          <CardTitle className="text-lg">{event.title}</CardTitle>
          <Badge variant="primary">{event.event_type}</Badge>
        </div>
        <p className="text-sm text-slate-500">{event.event_date}</p>
      </CardHeader>
      <CardContent>
        {event.description && <p className="text-sm text-slate-700 mb-4">{event.description}</p>}
        {event.value && (
          <div className="mb-4 bg-slate-50 p-3 rounded-md">
            <span className="text-sm font-medium text-slate-500">Extracted Value: </span>
            <span className="text-sm font-semibold">{event.value} {event.unit}</span>
          </div>
        )}
        {event.source_document_id && (
          <div>
            <h5 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Source Evidence</h5>
            <EvidenceItem 
              documentId={event.source_document_id} 
              page={event.source_page} 
              excerpt={event.source_excerpt} 
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
};
