import api from './api';
import { HealthEvent } from '../types';

export const eventsService = {
  getEvents: async (patientId: string, options?: { documentId?: string }): Promise<HealthEvent[]> => {
    let url = `/patients/${patientId}/events`;
    if (options?.documentId) {
      url += `?document_id=${options.documentId}`;
    }
    const response = await api.get(url);
    return response.data;
  },
  getEvent: async (id: string): Promise<HealthEvent> => {
    const response = await api.get(`/events/${id}`);
    return response.data;
  }
};
