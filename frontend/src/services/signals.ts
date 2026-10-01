import api from './api';
import { Signal } from '../types';

export const signalsService = {
  getSignals: async (patientId: string): Promise<Signal[]> => {
    const response = await api.get(`/patients/${patientId}/signals`);
    return response.data;
  },
  getSignal: async (id: string): Promise<Signal> => {
    const response = await api.get(`/signals/${id}`);
    return response.data;
  },
  reviewSignal: async (id: string, decision: string, comment?: string): Promise<Signal> => {
    const response = await api.post(`/signals/${id}/review`, { decision, comment });
    return response.data;
  }
};
