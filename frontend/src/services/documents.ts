import api from './api';
import { Document, DocumentDetail } from '../types';

export const documentsService = {
  getDocuments: async (patientId: string): Promise<Document[]> => {
    const response = await api.get(`/patients/${patientId}/documents`);
    return response.data;
  },
  getDocument: async (id: string): Promise<DocumentDetail> => {
    const response = await api.get(`/documents/${id}`);
    return response.data;
  },
  uploadDocument: async (patientId: string, file: File): Promise<Document> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post(`/patients/${patientId}/documents`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  getDocumentFile: async (id: string): Promise<Blob> => {
    const response = await api.get(`/documents/${id}/file`, {
      responseType: 'blob',
    });
    return response.data;
  }
};
