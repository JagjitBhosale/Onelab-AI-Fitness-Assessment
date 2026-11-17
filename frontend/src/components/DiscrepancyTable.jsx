import React, { useState, useMemo } from 'react';

const CATEGORY_BADGES = {
  matched: 'bg-green-100 text-green-800',
  unmatched_company: 'bg-red-100 text-red-800',
  unmatched_bank: 'bg-orange-100 text-orange-800',
  timing_difference: 'bg-blue-100 text-blue-800',
  rounding_difference: 'bg-yellow-100 text-yellow-800',
  duplicate_entry: 'bg-purple-100 text-purple-800',
  orphan_refund: 'bg-pink-100 text-pink-800',
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

export default function DiscrepancyTable({ discrepancies, onFilterChange }) {
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 15;

  const categories = useMemo(() => {
    const cats = new Set((discrepancies || []).map(d => d.category));
    return ['all', ...Array.from(cats).sort()];
  }, [discrepancies]);

  const filtered = useMemo(() => {
    let data = discrepancies || [];
    if (categoryFilter !== 'all') {
      data = data.filter(d => d.category === categoryFilter);
    }
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      data = data.filter(d =>
        d.transaction_id?.toLowerCase().includes(term) ||
        d.explanation?.toLowerCase().includes(term)
      );
    }
    return data;
  }, [discrepancies, categoryFilter, searchTerm]);

  const totalPages = Math.ceil(filtered.length / pageSize);
  const paged = filtered.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  const handleCategoryChange = (cat) => {
    setCategoryFilter(cat);
    setCurrentPage(1);
    if (onFilterChange) onFilterChange(cat === 'all' ? null : cat);
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-5">
        <h3 className="text-lg font-semibold text-gray-900">
          Discrepancy Analysis
          <span className="ml-2 text-sm font-normal text-gray-500">({filtered.length} records)</span>
        </h3>
        <div className="flex flex-wrap gap-2">
          <input
            type="text"
            placeholder="Search transactions..."
            value={searchTerm}
            onChange={(e) => { setSearchTerm(e.target.value); setCurrentPage(1); }}
            className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <select
            value={categoryFilter}
            onChange={(e) => handleCategoryChange(e.target.value)}
            className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
          >
            {categories.map(cat => (
              <option key={cat} value={cat}>
                {cat === 'all' ? 'All Categories' : (CATEGORY_LABELS[cat] || cat)}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-3 px-3 font-semibold text-gray-600">Transaction ID</th>
              <th className="text-right py-3 px-3 font-semibold text-gray-600">Company Amt</th>
              <th className="text-right py-3 px-3 font-semibold text-gray-600">Bank Amt</th>
              <th className="text-left py-3 px-3 font-semibold text-gray-600">Txn Date</th>
              <th className="text-left py-3 px-3 font-semibold text-gray-600">Settlement Date</th>
              <th className="text-right py-3 px-3 font-semibold text-gray-600">Difference</th>
              <th className="text-left py-3 px-3 font-semibold text-gray-600">Category</th>
              <th className="text-left py-3 px-3 font-semibold text-gray-600 max-w-xs">Explanation</th>
            </tr>
          </thead>
          <tbody>
            {paged.length === 0 ? (
              <tr>
                <td colSpan={8} className="text-center py-12 text-gray-400">
                  No discrepancies found
                </td>
              </tr>
            ) : (
              paged.map((d, i) => (
                <tr key={i} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                  <td className="py-3 px-3 font-mono text-xs text-gray-900">{d.transaction_id}</td>
                  <td className="py-3 px-3 text-right font-mono text-xs">
                    {d.company_amount ? `$${Number(d.company_amount).toFixed(2)}` : '—'}
                  </td>
                  <td className="py-3 px-3 text-right font-mono text-xs">
                    {d.bank_amount ? `$${Number(d.bank_amount).toFixed(2)}` : '—'}
                  </td>
                  <td className="py-3 px-3 text-xs text-gray-600">
                    {d.transaction_date ? d.transaction_date.split(' ')[0] : '—'}
                  </td>
                  <td className="py-3 px-3 text-xs text-gray-600">
                    {d.settlement_date ? d.settlement_date.split(' ')[0] : '—'}
                  </td>
                  <td className="py-3 px-3 text-right font-mono text-xs">
                    <span className={Number(d.difference) > 0 ? 'text-red-600 font-medium' : 'text-gray-500'}>
                      ${Number(d.difference).toFixed(2)}
                    </span>
                  </td>
                  <td className="py-3 px-3">
                    <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${CATEGORY_BADGES[d.category] || 'bg-gray-100 text-gray-700'}`}>
                      {CATEGORY_LABELS[d.category] || d.category}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-xs text-gray-600 max-w-xs truncate" title={d.explanation}>
                    {d.explanation}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-100">
          <p className="text-xs text-gray-500">
            Showing {(currentPage - 1) * pageSize + 1}–{Math.min(currentPage * pageSize, filtered.length)} of {filtered.length}
          </p>
          <div className="flex gap-1">
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1 text-xs rounded border border-gray-200 disabled:opacity-50 hover:bg-gray-50"
            >
              Prev
            </button>
            {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
              const pg = i + 1;
              return (
                <button
                  key={pg}
                  onClick={() => setCurrentPage(pg)}
                  className={`px-3 py-1 text-xs rounded border ${
                    currentPage === pg ? 'bg-blue-600 text-white border-blue-600' : 'border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  {pg}
                </button>
              );
            })}
            <button
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1 text-xs rounded border border-gray-200 disabled:opacity-50 hover:bg-gray-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
