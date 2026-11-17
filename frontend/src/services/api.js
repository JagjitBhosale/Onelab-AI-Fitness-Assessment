import axios from 'axios';

// Determine API base URL:
// 1. Explicit environment variable VITE_API_URL if configured
// 2. Default to deployed backend in production environments
// 3. Fallback to '/api' for local development via Vite proxy
const getBaseUrl = () => {
  if (import.meta.env.VITE_API_URL) {
    const raw = import.meta.env.VITE_API_URL.replace(/\/+$/, '');
    return raw.endsWith('/api') ? raw : `${raw}/api`;
  }
  if (typeof window !== 'undefined' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    return 'https://onelab-ai-fitness-assessment-tfyi.vercel.app/api';
  }
  return '/api';
};

const API_BASE = getBaseUrl();

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

export const generateData = () => api.post('/data/generate');

export const getCompanyTransactions = () => api.get('/data/company');

export const getBankSettlements = () => api.get('/data/bank');

export const runReconciliation = (category = null) => {
  const params = category ? { category } : {};
  return api.get('/reconcile', { params });
};

export const getCategories = () => api.get('/reconcile/categories');

export const getReport = () => api.get('/reports');

export const getMonthlyTotals = () => api.get('/reports/monthly');

export const exportCSV = () =>
  api.get('/reports/export/csv', { responseType: 'blob' });

export default api;
