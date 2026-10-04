import React from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { documentsService } from '../services/documents';
import api from '../services/api';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { RotateCw, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

export const DocumentDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  const queryClient = useQueryClient();
  const { data: doc, isLoading } = useQuery({
    queryKey: ['document', id],
    queryFn: () => documentsService.getDocument(id!),
    enabled: !!id,
    refetchInterval: (query) => ['UPLOADED', 'QUEUED', 'PROCESSING'].includes(query.state.data?.processing_status ?? '') ? 2000 : false,
  });

  const { data: events, isLoading: eventsLoading } = useQuery({
    queryKey: ['events', doc?.patient_id, { documentId: id }],
    queryFn: () => {
      // @ts-ignore
      return import('../services/events').then(m => m.eventsService.getEvents(doc!.patient_id, { documentId: id! }));
    },
    enabled: !!doc?.patient_id && !!id,
    refetchInterval: () => doc && ['UPLOADED', 'QUEUED', 'PROCESSING'].includes(doc.processing_status) ? 2000 : false,
  });

  const reprocessMutation = useMutation({
    mutationFn: () => api.post(`/documents/${id}/reprocess`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['document', id] });
    }
  });

  if (isLoading) return <div>Loading...</div>;
  if (!doc) return <div>Document not found</div>;

  return (
    <div className="h-full flex flex-col space-y-4">
      <div className="flex items-center justify-between shrink-0">
        <div className="flex items-center gap-4">
          <Link to="/app/documents" className="text-slate-400 hover:text-slate-600">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <h2 className="text-xl font-bold tracking-tight text-slate-900">{doc.original_filename}</h2>
          <Badge>{doc.processing_status}</Badge>
        </div>
        <Button variant="outline" size="sm" onClick={() => reprocessMutation.mutate()}>
          <RotateCw className="w-4 h-4 mr-2" />
          Reprocess
        </Button>
      </div>
      {doc.processing_error && <div role="status" className="rounded border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">{doc.processing_error}</div>}
      {reprocessMutation.isError && <div role="alert" className="text-sm text-red-700">Could not queue reprocessing. Verify your access and the backend status.</div>}

      <div className="flex-1 flex gap-6 min-h-0">
        <div className="w-1/2 flex flex-col bg-white border border-slate-200 rounded-lg overflow-hidden">
          <div className="bg-slate-50 px-4 py-2 border-b border-slate-200 font-medium text-sm text-slate-700">
            Extracted Text
          </div>
          <div className="flex-1 overflow-y-auto p-4 font-mono text-sm space-y-8 text-slate-800">
            {doc.pages.map((page) => (
              <div key={page.id} className="relative">
                <div className="sticky top-0 bg-white/90 py-1 mb-2 text-xs font-bold text-primary-600">Page {page.page_number}</div>
                <div className="whitespace-pre-wrap">{page.text_content}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="w-1/2 flex flex-col bg-slate-50 border border-slate-200 rounded-lg overflow-hidden">
          <div className="bg-white px-4 py-2 border-b border-slate-200 font-medium text-sm text-slate-700">
            Extracted Events
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            {eventsLoading ? (
               <div className="text-sm text-slate-500">Loading events...</div>
            ) : !events || events.length === 0 ? (
               <div className="text-sm text-slate-500">No events extracted yet.</div>
            ) : (
               <div className="space-y-4">
                 {events.map((event) => (
                   <div key={event.id} className="bg-white p-4 rounded border border-slate-200 shadow-sm">
                     <div className="flex justify-between items-start mb-2">
                       <h4 className="font-semibold text-slate-900">{event.title}</h4>
                       <Badge variant="outline">{event.event_type}</Badge>
                     </div>
                     {event.event_date && <div className="text-xs text-slate-500 mb-2">{event.event_date}</div>}
                     <p className="text-sm text-slate-700">{event.description}</p>
                   </div>
                 ))}
               </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
