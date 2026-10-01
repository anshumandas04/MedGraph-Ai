import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { dashboardService } from '../services/dashboard';
import { StatCard } from '../components/StatCard';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Skeleton } from '../components/ui/Skeleton';

export const ResearchPage: React.FC = () => {
  const { data: metrics, isLoading: isMetricsLoading } = useQuery({
    queryKey: ['research-metrics'],
    queryFn: dashboardService.getResearchDashboard,
  });

  const { data: evalData, isLoading: isEvalLoading } = useQuery({
    queryKey: ['research-evaluation'],
    queryFn: dashboardService.getEvaluation,
  });

  if (isMetricsLoading || isEvalLoading) return <div className="p-8"><Skeleton className="h-64" /></div>;

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">Research Dashboard</h2>
        <p className="text-slate-500 mt-1">System performance and evaluation metrics on synthetic datasets.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatCard title="Total Documents Processed" value={metrics?.documents_processed || 0} icon={null} />
        <StatCard title="Events Extracted" value={metrics?.events_extracted || 0} icon={null} />
        <StatCard title="Signals Generated" value={metrics?.signals_generated || 0} icon={null} />
        <StatCard title="Avg Extraction Confidence" value={`${Math.round((metrics?.avg_confidence || 0) * 100)}%`} icon={null} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Pipeline Evaluation (Synthetic Benchmark)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-8 text-center py-8">
              <div>
                <div className="text-4xl font-bold text-primary-600 mb-2">{(evalData?.f1 || 0).toFixed(2)}</div>
                <div className="text-sm font-medium text-slate-500">Overall F1 Score</div>
              </div>
              <div>
                <div className="text-4xl font-bold text-emerald-600 mb-2">{(evalData?.precision || 0).toFixed(2)}</div>
                <div className="text-sm font-medium text-slate-500">Precision</div>
              </div>
              <div>
                <div className="text-4xl font-bold text-blue-600 mb-2">{(evalData?.recall || 0).toFixed(2)}</div>
                <div className="text-sm font-medium text-slate-500">Recall</div>
              </div>
              <div>
                <div className="text-4xl font-bold text-amber-600 mb-2">{(evalData?.evidence_accuracy || 0).toFixed(2)}</div>
                <div className="text-sm font-medium text-slate-500">Evidence Accuracy</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
