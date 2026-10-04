import React, { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { usePatient } from '../hooks/usePatient';
import { eventsService } from '../services/events';
import { ReactFlow, Controls, Background, Node, Edge } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import api from '../services/api';
import { ErrorState } from '../components/ErrorState';
import { EmptyState } from '../components/EmptyState';

const fetchRelationships = async (patientId: string) => {
  const events = await eventsService.getEvents(patientId);
  const relationsResponse = await Promise.all(
    events.map(e => api.get(`/events/${e.id}/relationships`).then(res => res.data))
  );
  return { events, relationships: relationsResponse.flat() };
};

export const GraphPage: React.FC = () => {
  const { selectedPatientId } = usePatient();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['graph', selectedPatientId],
    queryFn: () => fetchRelationships(selectedPatientId!),
    enabled: !!selectedPatientId,
  });

  const { nodes, edges } = useMemo(() => {
    if (!data) return { nodes: [], edges: [] };

    // Group items basically just for visual spread
    const nodes: Node[] = data.events.map((event, index) => ({
      id: event.id,
      // Keep the complete graph inside the viewport at desktop and laptop widths.
      position: { x: (index % 3) * 145, y: Math.floor(index / 3) * 90 },
      data: { label: `${event.title}\n(${event.event_type})` },
      style: {
        background: '#fff',
        border: '1px solid #e2e8f0',
        borderRadius: '8px',
        padding: '10px',
        minWidth: '128px',
        maxWidth: '138px',
        fontSize: '11px',
        lineHeight: 1.35,
        whiteSpace: 'normal',
        overflowWrap: 'anywhere',
        wordBreak: 'break-word',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
      }
    }));

    const edges: Edge[] = data.relationships.map((rel: any) => ({
      id: rel.id,
      source: rel.source_event_id,
      target: rel.target_event_id,
      label: rel.relationship_type,
      animated: true,
      style: { stroke: '#94a3b8' },
    }));

    return { nodes, edges };
  }, [data]);

  if (!selectedPatientId) return <div className="p-8 text-center text-slate-500">Please select a patient.</div>;
  if (isLoading) return <div className="p-8 text-center text-slate-500">Loading graph...</div>;
  if (error) return <ErrorState title="Knowledge graph failed to load" message="The patient events or their relationships could not be loaded." error={error} onRetry={() => { void refetch(); }} />;
  if (!data || data.events.length === 0) return <EmptyState title="No graph events yet" description="Upload and process a document containing health events to build this graph." />;

  return (
    <div className="flex h-[calc(100vh-10rem)] min-h-[480px] w-full flex-col overflow-hidden bg-slate-50">
      <div className="p-6 shrink-0 border-b border-slate-200">
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">Healthcare Journey Graph</h2>
        <p className="text-sm text-slate-500 mt-1">
          Visualizing clinical events and their relationships.
        </p>
      </div>
      <div className="relative min-h-[360px] w-full flex-1">
        <ReactFlow nodes={nodes} edges={edges} fitView fitViewOptions={{ padding: 0.2, maxZoom: 1 }}>
          <Background />
          <Controls />
        </ReactFlow>
      </div>
    </div>
  );
};
