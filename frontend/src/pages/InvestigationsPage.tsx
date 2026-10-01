import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { investigationsService } from '../services/investigations';
import { usePatient } from '../hooks/usePatient';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Skeleton } from '../components/ui/Skeleton';
import { ErrorState } from '../components/ErrorState';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Badge } from '../components/ui/Badge';

export const InvestigationsPage: React.FC = () => {
  const { selectedPatientId } = usePatient();

  const { data, isLoading, error } = useQuery({
    queryKey: ['investigations', selectedPatientId],
    queryFn: () => investigationsService.getInvestigations(selectedPatientId!),
    enabled: !!selectedPatientId,
  });

  if (!selectedPatientId) return <div>Select a patient</div>;
  if (isLoading) return <div className="space-y-4 p-6"><Skeleton className="h-64 w-full" /></div>;
  if (error || !data) return <ErrorState />;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">Investigations</h2>
        <p className="text-slate-500 mt-1">Lab results and diagnostic reports over time.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {data.map(inv => (
          <Card key={inv.id}>
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle>{inv.name}</CardTitle>
                <Badge>{inv.category}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="h-64 mt-4">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={inv.results.sort((a,b) => new Date(a.test_date || '').getTime() - new Date(b.test_date || '').getTime())}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="test_date" tickFormatter={(t) => t?.substring(0,10)} />
                    <YAxis />
                    <Tooltip />
                    <Line 
                      type="monotone" 
                      dataKey="value" 
                      stroke="#0ea5e9" 
                      strokeWidth={2}
                      activeDot={{ r: 8 }} 
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};
