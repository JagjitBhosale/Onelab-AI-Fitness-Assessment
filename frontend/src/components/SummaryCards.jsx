import React from 'react';

const CARD_CONFIGS = [
  { key: 'total_company_transactions', label: 'Company Transactions', icon: '📋', color: 'blue' },
  { key: 'total_bank_settlements', label: 'Bank Settlements', icon: '🏦', color: 'indigo' },
  { key: 'matched_count', label: 'Matched', icon: '✅', color: 'green' },
  { key: 'unmatched_total', label: 'Unmatched', icon: '❌', color: 'red', computed: true },
  { key: 'total_amount_difference', label: 'Amount Difference', icon: '💰', color: 'amber', isAmount: true },
  { key: 'reconciliation_success_rate', label: 'Success Rate', icon: '📊', color: 'emerald', isPercent: true },
];

const COLOR_MAP = {
  blue: 'bg-blue-50 border-blue-200 text-blue-700',
  indigo: 'bg-indigo-50 border-indigo-200 text-indigo-700',
  green: 'bg-green-50 border-green-200 text-green-700',
  red: 'bg-red-50 border-red-200 text-red-700',
  amber: 'bg-amber-50 border-amber-200 text-amber-700',
  emerald: 'bg-emerald-50 border-emerald-200 text-emerald-700',
};

const ICON_BG = {
  blue: 'bg-blue-100',
  indigo: 'bg-indigo-100',
  green: 'bg-green-100',
  red: 'bg-red-100',
  amber: 'bg-amber-100',
  emerald: 'bg-emerald-100',
};

export default function SummaryCards({ summary }) {
  if (!summary) return null;

  const unmatched = (summary.unmatched_company_count || 0) + (summary.unmatched_bank_count || 0);

  const getValue = (cfg) => {
    if (cfg.computed) return unmatched;
    if (cfg.isAmount) return `$${Number(summary[cfg.key] || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
    if (cfg.isPercent) return `${summary[cfg.key] || 0}%`;
    return summary[cfg.key] || 0;
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-8">
      {CARD_CONFIGS.map((cfg, i) => (
        <div
          key={cfg.key}
          className={`bg-white rounded-xl border shadow-sm p-5 animate-slide-up ${COLOR_MAP[cfg.color].split(' ')[1]}`}
          style={{ animationDelay: `${i * 80}ms` }}
        >
          <div className="flex items-center justify-between mb-3">
            <span className={`w-10 h-10 rounded-lg flex items-center justify-center text-lg ${ICON_BG[cfg.color]}`}>
              {cfg.icon}
            </span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{getValue(cfg)}</p>
          <p className="text-xs font-medium text-gray-500 mt-1">{cfg.label}</p>
        </div>
      ))}
    </div>
  );
}
