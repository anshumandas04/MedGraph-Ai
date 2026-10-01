import api from './api';
import { Medication } from '../types';

export const medicationsService = {
  getMedications: async (patientId: string): Promise<Medication[]> => {
    const response = await api.get(`/patients/${patientId}/medications`);
    return response.data;
  }
};
