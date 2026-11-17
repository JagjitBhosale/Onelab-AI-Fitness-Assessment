import React from 'react';
import SummaryCards from './SummaryCards';
import Charts from './Charts';
import DiscrepancyTable from './DiscrepancyTable';
import Reports from './Reports';

export default function Dashboard({ data, loading, error }) {
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24">
        <svg className="w-12 h-12 text-blue-500 animate-spin mb-4" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <p className="text-gray-500 font-medium">Running reconciliation...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
        <p className="text-red-700 font-medium mb-2">Error</p>
        <p className="text-red-600 text-sm">{error}</p>
        <p className="text-red-500 text-xs mt-2">Try clicking "Regenerate Data" to generate datasets first.</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center py-24">
        <p className="text-gray-400 text-lg">Click "Regenerate Data" to start</p>
      </div>
    );
  }

  const { reconciliation, report, monthlyTotals } = data;

  return (
    <div className="animate-fade-in">
      {/* Tab Navigation */}
      <SummaryCards summary={reconciliation?.summary} />
      <Charts
        summary={reconciliation?.summary}
        discrepancies={reconciliation?.discrepancies}
        monthlyTotals={monthlyTotals}
      />
      <DiscrepancyTable discrepancies={reconciliation?.discrepancies} />
      <Reports report={report} monthlyTotals={monthlyTotals} />
    </div>
  );
}
