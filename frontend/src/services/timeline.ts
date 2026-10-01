import api from './api';
import { TimelineEntry } from '../types';

export const timelineService = {
  getTimeline: async (patientId: string): Promise<TimelineEntry[]> => {
    const response = await api.get(`/patients/${patientId}/timeline`);
    return response.data;
  }
};
