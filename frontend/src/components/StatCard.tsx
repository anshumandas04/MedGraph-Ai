import React from 'react';
import { Card, CardContent } from './ui/Card';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  description?: string;
  trend?: string;
}

export const StatCard: React.FC<StatCardProps> = ({ title, value, icon, description, trend }) => {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div className="text-slate-500">{icon}</div>
        </div>
        <div className="mt-4">
          <h3 className="text-sm font-medium text-slate-500">{title}</h3>
          <div className="mt-1 flex items-baseline gap-2">
            <p className="text-2xl font-semibold text-slate-900">{value}</p>
            {trend && <span className="text-sm font-medium text-emerald-600">{trend}</span>}
          </div>
          {description && <p className="mt-1 text-sm text-slate-500">{description}</p>}
        </div>
      </CardContent>
    </Card>
  );
};
