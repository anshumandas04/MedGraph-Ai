import React from 'react';
import { useAuth } from '../hooks/useAuth';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';

export const SettingsPage: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="max-w-3xl space-y-6">
      <h2 className="text-2xl font-bold tracking-tight text-slate-900">Settings</h2>
      
      <Card>
        <CardHeader>
          <CardTitle>Profile Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium text-slate-500 block">Full Name</label>
            <div className="mt-1 text-slate-900">{user?.full_name}</div>
          </div>
          <div>
            <label className="text-sm font-medium text-slate-500 block">Email</label>
            <div className="mt-1 text-slate-900">{user?.email}</div>
          </div>
          <div>
            <label className="text-sm font-medium text-slate-500 block">Role</label>
            <div className="mt-1 text-slate-900">{user?.role}</div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
