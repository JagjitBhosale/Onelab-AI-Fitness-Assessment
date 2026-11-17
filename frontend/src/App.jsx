import React, { useState, useEffect, useCallback } from 'react';
import Layout from './components/Layout';
import Dashboard from './components/Dashboard';
import { generateData, runReconciliation, getReport, getMonthlyTotals } from './services/api';

export default function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [reconRes, reportRes, monthlyRes] = await Promise.all([
        runReconciliation(),
        getReport(),
        getMonthlyTotals(),
      ]);
      setData({
        reconciliation: reconRes.data,
        report: reportRes.data,
        monthlyTotals: monthlyRes.data,
      });
    } catch (err) {
      console.error('Failed to load data:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleRegenerate = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await generateData();
      await loadData();
    } catch (err) {
      console.error('Failed to regenerate:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to regenerate data');
      setLoading(false);
    }
  }, [loadData]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  return (
    <Layout onRegenerate={handleRegenerate} loading={loading}>
      <Dashboard data={data} loading={loading} error={error} />
    </Layout>
  );
}
