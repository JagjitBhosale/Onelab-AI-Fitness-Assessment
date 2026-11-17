import React from 'react';
import { exportCSV } from '../services/api';

export default function Reports({ report, monthlyTotals }) {
  if (!report) return null;

  const handleExportCSV = async () => {
    try {
      const response = await exportCSV();
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'discrepancy_report.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert('Failed to export CSV: ' + err.message);
    }
  };

  return (
    <div className="space-y-6">
      {/* Reconciliation Summary Report */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <div className="flex justify-between items-center mb-5">
          <h3 className="text-lg font-semibold text-gray-900">Reconciliation Report</h3>
          <button
            onClick={handleExportCSV}
            className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Export CSV
          </button>
        </div>

        {/* Explanation */}
        <div className="bg-blue-50 rounded-lg p-4 mb-6 border border-blue-100">
          <h4 className="font-medium text-blue-900 mb-2">Analysis Summary</h4>
          <div className="text-sm text-blue-800 whitespace-pre-line leading-relaxed">
            {report.explanation}
          </div>
        </div>
      </div>

      {/* Monthly Totals Table */}
      {monthlyTotals && monthlyTotals.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Monthly Reconciliation Totals</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-semibold text-gray-600">Month</th>
                  <th className="text-right py-3 px-4 font-semibold text-gray-600">Company Total</th>
                  <th className="text-right py-3 px-4 font-semibold text-gray-600">Bank Total</th>
                  <th className="text-right py-3 px-4 font-semibold text-gray-600">Difference</th>
                  <th className="text-right py-3 px-4 font-semibold text-gray-600">Matched</th>
                  <th className="text-right py-3 px-4 font-semibold text-gray-600">Unmatched</th>
                </tr>
              </thead>
              <tbody>
                {monthlyTotals.map((m, i) => (
                  <tr key={i} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-3 px-4 font-medium">{m.month}</td>
                    <td className="py-3 px-4 text-right font-mono">
                      ${Number(m.company_total).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-4 text-right font-mono">
                      ${Number(m.bank_total).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-4 text-right font-mono">
                      <span className={Number(m.difference) > 0 ? 'text-red-600 font-medium' : 'text-green-600'}>
                        ${Number(m.difference).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">{m.matched_count}</td>
                    <td className="py-3 px-4 text-right">
                      <span className={m.unmatched_count > 0 ? 'text-red-600' : ''}>{m.unmatched_count}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
