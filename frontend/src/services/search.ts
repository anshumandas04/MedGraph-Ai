import api from './api';
import { SearchResponse } from '../types';

export const searchService = {
  searchRecords: async (patientId: string, query: string): Promise<SearchResponse> => {
    const response = await api.post(`/patients/${patientId}/search`, { query });
    return response.data;
  }
};
