import api from './api';
import { User } from '../types';

export const authService = {
  login: async (email: string, password: string):Promise<{access_token: string, user: User}> => {
    const response = await api.post('/auth/login', { email, password });
    return response.data;
  },
  register: async (data: any):Promise<{access_token: string, user: User}> => {
    const response = await api.post('/auth/register', data);
    return response.data;
  },
  getMe: async ():Promise<User> => {
    const response = await api.get('/auth/me');
    return response.data;
  }
};
