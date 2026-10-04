import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { signalsService } from '../services/signals';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { EvidenceItem } from '../components/EvidenceItem';
import { ArrowLeft, Check, X } from 'lucide-react';
import { Link } from 'react-router-dom';

export const SignalDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [comment, setComment] = useState('');

  const { data: signal, isLoading } = useQuery({
    queryKey: ['signal', id],
    queryFn: () => signalsService.getSignal(id!),
    enabled: !!id,
  });

  const reviewMutation = useMutation({
    mutationFn: ({ decision, comment: review_comment }: { decision: string, comment?: string }) => 
      signalsService.reviewSignal(id!, decision, review_comment),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['signal', id] });
      queryClient.invalidateQueries({ queryKey: ['signals'] });
      navigate('/app/signals');
    },
  });

  if (isLoading) return <div>Loading...</div>;
  if (!signal) return <div>Signal not found</div>;

  return (
    <div className="max-w-3xl mx-auto py-6 space-y-8">
      <Link to="/app/signals" className="inline-flex items-center text-sm font-medium text-slate-500 hover:text-slate-900">
        <ArrowLeft className="w-4 h-4 mr-1" />
        Back to Signals
      </Link>

      <div className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
        <div className="p-6 border-b border-slate-200">
          <div className="flex justify-between items-start mb-4">
            <h2 className="text-xl font-bold text-slate-900">{signal.title}</h2>
            <div className="flex gap-2">
              <Badge variant={signal.severity === 'HIGH' ? 'error' : 'warning'}>{signal.severity} Severity</Badge>
              <Badge variant="outline">{signal.status}</Badge>
            </div>
          </div>
          <p className="text-slate-700">{signal.description}</p>
        </div>

        <div className="p-6 bg-slate-50 border-b border-slate-200">
          <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-4">Evidence</h3>
          <div className="space-y-4">
            {signal.evidence.map((ev) => (
              <div key={ev.id} className="relative pl-4 border-l-4 border-slate-300">
                <Badge variant={ev.role === 'CONFLICTING' ? 'error' : 'primary'} className="mb-2">
                  {ev.role}
                </Badge>
                <EvidenceItem 
                  documentId={ev.document_id!} 
                  page={ev.page_number} 
                  excerpt={ev.excerpt} 
                />
              </div>
            ))}
          </div>
        </div>

        {signal.status === 'OPEN' && (
          <div className="p-6">
            <h3 className="text-sm font-semibold text-slate-900 mb-4">Review Signal</h3>
            <textarea
              className="w-full border border-slate-300 rounded-md p-3 text-sm focus:ring-2 focus:ring-primary-500 mb-4"
              rows={3}
              placeholder="Add optional review notes..."
              value={comment}
              onChange={(e) => setComment(e.target.value)}
            />
            <div className="flex gap-3">
              <Button 
                onClick={() => reviewMutation.mutate({ decision: 'VERIFY', comment })}
                className="bg-emerald-600 hover:bg-emerald-700 focus-visible:ring-emerald-600"
              >
                <Check className="w-4 h-4 mr-2" /> Verify Issue
              </Button>
              <Button 
                variant="outline"
                onClick={() => reviewMutation.mutate({ decision: 'DISMISS', comment })}
              >
                <X className="w-4 h-4 mr-2" /> Dismiss
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
