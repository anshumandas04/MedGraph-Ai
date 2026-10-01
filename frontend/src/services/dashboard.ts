import api from './api';
import { DashboardData, ResearchDashboard, EvaluationResult } from '../types';

export const dashboardService = {
  getDashboard: async (patientId: string): Promise<DashboardData> => {
    const response = await api.get(`/patients/${patientId}/dashboard`);
    return response.data;
  },
  getResearchDashboard: async (): Promise<ResearchDashboard> => {
    const response = await api.get(`/admin/dashboard`);
    return response.data;
  },
  getEvaluation: async (): Promise<EvaluationResult> => {
    const response = await api.get(`/admin/evaluation`);
    return response.data;
  }
};
