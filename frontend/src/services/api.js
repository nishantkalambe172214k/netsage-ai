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

export const getDashboard = async () => {
  const response = await api.get('/dashboard/');
  return response.data;
};

export const getCases = async (statusFilter = null, categoryFilter = null) => {
  const params = {};
  if (statusFilter) params.status_filter = statusFilter;
  if (categoryFilter) params.category_filter = categoryFilter;
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

export const seedDatabaseCases = async () => {
  const response = await api.post('/cases/seed');
  return response.data;
};

export const runRuleCheck = async (idOrCaseId) => {
  const response = await api.post(`/cases/${idOrCaseId}/check-rules`);
  return response.data;
};

export const runAIDiagnosis = async (idOrCaseId) => {
  const response = await api.post(`/cases/${idOrCaseId}/diagnose`);
  return response.data;
};

export const runCaseAnalysis = async (idOrCaseId) => {
  const response = await api.post(`/cases/${idOrCaseId}/analyze`);
  return response.data;
};

export const submitReview = async (idOrCaseId, reviewData) => {
  const response = await api.post(`/reviews/${idOrCaseId}`, reviewData);
  return response.data;
};

export const getCaseReviews = async (idOrCaseId) => {
  const response = await api.get(`/reviews/${idOrCaseId}`);
  return response.data;
};

export const submitVerification = async (idOrCaseId, verificationData) => {
  const response = await api.post(`/verification/${idOrCaseId}`, verificationData);
  return response.data;
};

export const getCaseVerification = async (idOrCaseId) => {
  const response = await api.get(`/verification/${idOrCaseId}`);
  return response.data;
};

export const getResponsibleAILog = async () => {
  const response = await api.get('/responsible-ai/');
  return response.data;
};

export const seedResponsibleAIExamples = async () => {
  const response = await api.post('/responsible-ai/seed-examples');
  return response.data;
};

export default api;
