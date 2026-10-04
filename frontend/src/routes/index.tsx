import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { PatientProvider } from '../hooks/usePatient';

import { AppLayout } from '../layouts/AppLayout';
import { AuthLayout } from '../layouts/AuthLayout';

import { LandingPage } from '../pages/LandingPage';
import { LoginPage } from '../pages/LoginPage';
import { RegisterPage } from '../pages/RegisterPage';
import { DashboardPage } from '../pages/DashboardPage';
import { TimelinePage } from '../pages/TimelinePage';
import { GraphPage } from '../pages/GraphPage';
import { DocumentsPage } from '../pages/DocumentsPage';
import { DocumentDetailPage } from '../pages/DocumentDetailPage';
import { SignalsPage } from '../pages/SignalsPage';
import { SignalDetailPage } from '../pages/SignalDetailPage';
import { MedicationsPage } from '../pages/MedicationsPage';
import { InvestigationsPage } from '../pages/InvestigationsPage';
import { AskMedGraphPage } from '../pages/AskMedGraphPage';
import { ResearchPage } from '../pages/ResearchPage';
import { SettingsPage } from '../pages/SettingsPage';
import { NotFoundPage } from '../pages/NotFoundPage';
import { DiagnosticsPage } from '../pages/DiagnosticsPage';

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, isLoading } = useAuth();
  
  if (isLoading) return <div className="h-screen flex items-center justify-center">Loading...</div>;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  
  return <PatientProvider>{children}</PatientProvider>;
};

const AdminRoute = ({ children }: { children: React.ReactNode }) => {
  const { user, isLoading } = useAuth();
  if (isLoading) return <div className="h-screen flex items-center justify-center">Loading...</div>;
  if (user?.role !== 'ADMIN') return <Navigate to="/app/dashboard" replace />;
  return <>{children}</>;
};

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Route>

      <Route path="/app" element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
        <Route index element={<Navigate to="dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="timeline" element={<TimelinePage />} />
        <Route path="graph" element={<GraphPage />} />
        <Route path="documents" element={<DocumentsPage />} />
        <Route path="documents/:id" element={<DocumentDetailPage />} />
        <Route path="signals" element={<SignalsPage />} />
        <Route path="signals/:id" element={<SignalDetailPage />} />
        <Route path="medications" element={<MedicationsPage />} />
        <Route path="investigations" element={<InvestigationsPage />} />
        <Route path="ask" element={<AskMedGraphPage />} />
        <Route path="research" element={<AdminRoute><ResearchPage /></AdminRoute>} />
        <Route path="diagnostics" element={<AdminRoute><DiagnosticsPage /></AdminRoute>} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
