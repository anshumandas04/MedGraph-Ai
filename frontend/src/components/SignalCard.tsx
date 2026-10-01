import React from 'react';
import { Signal } from '../types';
import { Card, CardContent } from './ui/Card';
import { Badge } from './ui/Badge';
import { AlertTriangle, Info, AlertCircle } from 'lucide-react';
import { Link } from 'react-router-dom';

export const SignalCard: React.FC<{ signal: Signal }> = ({ signal }) => {
  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'HIGH': return <Badge variant="error">High Severity</Badge>;
      case 'MEDIUM': return <Badge variant="warning">Medium Severity</Badge>;
      default: return <Badge variant="info">Low Severity</Badge>;
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'HIGH': return <AlertCircle className="w-5 h-5 text-red-500" />;
      case 'MEDIUM': return <AlertTriangle className="w-5 h-5 text-amber-500" />;
      default: return <Info className="w-5 h-5 text-blue-500" />;
    }
  };

  return (
    <Card className="hover:border-primary-300 transition-colors">
      <Link to={`/app/signals/${signal.id}`}>
        <CardContent className="p-4 flex gap-4 items-start">
          <div className="mt-1">{getSeverityIcon(signal.severity)}</div>
          <div className="flex-1">
            <div className="flex justify-between items-start">
              <h4 className="font-medium text-slate-900">{signal.title}</h4>
              {getSeverityBadge(signal.severity)}
            </div>
            <p className="text-sm text-slate-600 mt-1 line-clamp-2">{signal.description}</p>
            <div className="flex gap-3 mt-3 text-xs text-slate-500">
              <span>{signal.evidence?.length || 0} evidence pieces</span>
              <span>{Math.round((signal.confidence || 0) * 100)}% confidence</span>
              <Badge variant="outline">{signal.status}</Badge>
            </div>
          </div>
        </CardContent>
      </Link>
    </Card>
  );
};
