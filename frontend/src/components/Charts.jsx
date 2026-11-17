import React from 'react';
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from 'recharts';

const CATEGORY_COLORS = {
  matched: '#22c55e',
  unmatched_company: '#ef4444',
  unmatched_bank: '#f97316',
  timing_difference: '#3b82f6',
  rounding_difference: '#eab308',
  duplicate_entry: '#a855f7',
  orphan_refund: '#ec4899',
};

const CATEGORY_LABELS = {
  matched: 'Matched',
  unmatched_company: 'Unmatched (Company)',
  unmatched_bank: 'Unmatched (Bank)',
  timing_difference: 'Timing Difference',
  rounding_difference: 'Rounding Difference',
  duplicate_entry: 'Duplicate Entry',
  orphan_refund: 'Orphan Refund',
};

export default function Charts({ summary, discrepancies, monthlyTotals }) {
  // Pie chart data from summary
  const pieData = [];
  if (summary) {
    if (summary.matched_count > 0)
      pieData.push({ name: 'Matched', value: summary.matched_count, color: CATEGORY_COLORS.matched });
    if (summary.unmatched_company_count > 0)
      pieData.push({ name: 'Unmatched (Company)', value: summary.unmatched_company_count, color: CATEGORY_COLORS.unmatched_company });
    if (summary.unmatched_bank_count > 0)
      pieData.push({ name: 'Unmatched (Bank)', value: summary.unmatched_bank_count, color: CATEGORY_COLORS.unmatched_bank });
    if (summary.timing_difference_count > 0)
      pieData.push({ name: 'Timing Diff', value: summary.timing_difference_count, color: CATEGORY_COLORS.timing_difference });
    if (summary.rounding_difference_count > 0)
      pieData.push({ name: 'Rounding Diff', value: summary.rounding_difference_count, color: CATEGORY_COLORS.rounding_difference });
    if (summary.duplicate_count > 0)
      pieData.push({ name: 'Duplicates', value: summary.duplicate_count, color: CATEGORY_COLORS.duplicate_entry });
    if (summary.orphan_refund_count > 0)
      pieData.push({ name: 'Orphan Refunds', value: summary.orphan_refund_count, color: CATEGORY_COLORS.orphan_refund });
  }

  // Bar chart data from monthly totals
  const barData = (monthlyTotals || []).map(m => ({
    month: m.month,
    Company: parseFloat(m.company_total) || 0,
    Bank: parseFloat(m.bank_total) || 0,
  }));

  // Discrepancy breakdown by category
  const catCounts = {};
  (discrepancies || []).forEach(d => {
    const cat = d.category;
    catCounts[cat] = (catCounts[cat] || 0) + 1;
  });
  const breakdownData = Object.entries(catCounts).map(([cat, count]) => ({
    category: CATEGORY_LABELS[cat] || cat,
    count,
    fill: CATEGORY_COLORS[cat] || '#6b7280',
  }));

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
      {/* Reconciliation Status Pie */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Reconciliation Status</h3>
        {pieData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={3}
                dataKey="value"
                label={({ name, value }) => `${name}: ${value}`}
              >
                {pieData.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-gray-400 text-center py-16">No data available</p>
        )}
      </div>

      {/* Monthly Comparison Bar */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Monthly Totals Comparison</h3>
        {barData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="month" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip formatter={(v) => `$${v.toLocaleString()}`} />
              <Legend />
              <Bar dataKey="Company" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Bank" fill="#22c55e" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-gray-400 text-center py-16">No data available</p>
        )}
      </div>

      {/* Discrepancy Breakdown */}
      {breakdownData.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 lg:col-span-2">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Discrepancy Breakdown</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={breakdownData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis type="number" tick={{ fontSize: 12 }} />
              <YAxis type="category" dataKey="category" width={150} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                {breakdownData.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
