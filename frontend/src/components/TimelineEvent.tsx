import React, { useState } from 'react';
import { HealthEvent } from '../types';
import { Badge } from './ui/Badge';
import { Stethoscope, Pill, FlaskConical, Calendar, FileText, ChevronDown, ChevronUp } from 'lucide-react';
import { EvidenceItem } from './EvidenceItem';

interface TimelineEventProps {
  event: HealthEvent;
}

const getEventIcon = (type: string) => {
  switch (type.toUpperCase()) {
    case 'CONSULTATION': return <Stethoscope className="w-5 h-5" />;
    case 'MEDICATION': return <Pill className="w-5 h-5" />;
    case 'INVESTIGATION': return <FlaskConical className="w-5 h-5" />;
    case 'FOLLOW_UP': return <Calendar className="w-5 h-5" />;
    default: return <FileText className="w-5 h-5" />;
  }
};

export const TimelineEvent: React.FC<TimelineEventProps> = ({ event }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="relative pl-8 py-4 border-l-2 border-slate-200 last:border-0 group">
      <div className="absolute -left-[11px] top-4 p-1 rounded-full bg-white border-2 border-primary-500 text-primary-600">
        {getEventIcon(event.event_type)}
      </div>
      
      <div className="bg-white rounded-lg border border-slate-200 p-4 shadow-sm hover:shadow-md transition-shadow">
        <div className="flex justify-between items-start cursor-pointer" onClick={() => setExpanded(!expanded)}>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="primary">{event.event_type}</Badge>
              <span className="text-sm text-slate-500">{event.event_date}</span>
              {event.confidence && (
                <span className="text-xs text-slate-400">
                  {Math.round(event.confidence * 100)}% conf
                </span>
              )}
            </div>
            <h4 className="text-base font-medium text-slate-900">{event.title}</h4>
            {event.value && (
              <p className="text-sm font-semibold text-slate-700 mt-1">
                Value: {event.value} {event.unit}
              </p>
            )}
          </div>
          <button className="text-slate-400 hover:text-slate-600">
            {expanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </button>
        </div>

        {expanded && (
          <div className="mt-4 pt-4 border-t border-slate-100">
            {event.description && (
              <p className="text-sm text-slate-600 mb-4">{event.description}</p>
            )}
            
            {event.source_document_id && (
              <div className="mt-2">
                <h5 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Evidence</h5>
                <EvidenceItem 
                  documentId={event.source_document_id} 
                  page={event.source_page} 
                  excerpt={event.source_excerpt} 
                />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
