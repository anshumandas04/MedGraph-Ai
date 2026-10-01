import React, { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { usePatient } from '../hooks/usePatient';
import { eventsService } from '../services/events';
import { ReactFlow, Controls, Background, MiniMap, Node, Edge } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import api from '../services/api';

const fetchRelationships = async (patientId: string) => {
  const events = await eventsService.getEvents(patientId);
  const relationsResponse = await Promise.all(
    events.map(e => api.get(`/events/${e.id}/relationships`).then(res => res.data))
  );
  return { events, relationships: relationsResponse.flat() };
};

export const GraphPage: React.FC = () => {
  const { selectedPatientId } = usePatient();

  const { data, isLoading } = useQuery({
    queryKey: ['graph', selectedPatientId],
    queryFn: () => fetchRelationships(selectedPatientId!),
    enabled: !!selectedPatientId,
  });

  const { nodes, edges } = useMemo(() => {
    if (!data) return { nodes: [], edges: [] };

    // Group items basically just for visual spread
    const nodes: Node[] = data.events.map((event, index) => ({
      id: event.id,
      position: { x: (index % 5) * 250, y: Math.floor(index / 5) * 150 },
      data: { label: `${event.title}\n(${event.event_type})` },
      style: {
        background: '#fff',
        border: '1px solid #e2e8f0',
        borderRadius: '8px',
        padding: '10px',
        fontSize: '12px',
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

  return (
    <div className="h-full w-full bg-slate-50 flex flex-col">
      <div className="p-6 shrink-0 border-b border-slate-200">
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">Healthcare Journey Graph</h2>
        <p className="text-sm text-slate-500 mt-1">
          Visualizing clinical events and their relationships.
        </p>
      </div>
      <div className="flex-1 w-full relative">
        <ReactFlow nodes={nodes} edges={edges} fitView>
          <Background />
          <Controls />
          <MiniMap />
        </ReactFlow>
      </div>
    </div>
  );
};
