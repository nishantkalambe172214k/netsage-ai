import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const checkHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};

export const getCases = async (statusFilter = null) => {
  const params = statusFilter ? { status_filter: statusFilter } : {};
  const response = await api.get('/cases/', { params });
  return response.data;
};

export const getCaseDetail = async (idOrCaseId) => {
  const response = await api.get(`/cases/${idOrCaseId}`);
  return response.data;
};

export const createCase = async (caseData) => {
  const response = await api.post('/cases/', caseData);
  return response.data;
};

export const submitReview = async (reviewData) => {
  const response = await api.post('/reviews/', reviewData);
  return response.data;
};

export const recordVerification = async (verificationData) => {
  const response = await api.post('/verification/', verificationData);
  return response.data;
};

export default api;
