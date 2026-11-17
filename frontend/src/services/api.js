import axios from 'axios';

const API_BASE = '/api';

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
