import api from './api';
import { Patient, PatientSummary } from '../types';

export const patientsService = {
  getPatients: async (): Promise<Patient[]> => {
    const response = await api.get('/patients');
    return response.data;
  },
  getPatient: async (id: string): Promise<Patient> => {
    const response = await api.get(`/patients/${id}`);
    return response.data;
  },
  getPatientSummary: async (id: string): Promise<PatientSummary> => {
    const response = await api.get(`/patients/${id}/summary`);
    return response.data;
  }
};
