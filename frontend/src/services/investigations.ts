import api from './api';
import { Investigation } from '../types';

export const investigationsService = {
  getInvestigations: async (patientId: string): Promise<Investigation[]> => {
    const response = await api.get(`/patients/${patientId}/investigations`);
    return response.data;
  }
};
