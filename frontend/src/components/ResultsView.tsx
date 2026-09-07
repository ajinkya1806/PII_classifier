import { useEffect, useMemo, useState } from 'react';
import { api } from '../api';
import type { ScanResult } from '../api';
import FieldDetail from './FieldDetail';

interface Props {
  jobId: string;
  onBack: () => void;
}

const CATEGORY_CONFIG: Record<string, { badge: string; color: string; icon: string }> = {
  'Financial Sensitive (RBI-DADP)': { badge: 'badge-financial', color: 'text-red-400', icon: '🔴' },
  'Sensitive Personal Data (DPDP)': { badge: 'badge-sensitive', color: 'text-orange-400', icon: '🟠' },
  'PII': { badge: 'badge-pii', color: 'text-yellow-400', icon: '🟡' },
  'Non-Sensitive': { badge: 'badge-non-sensitive', color: 'text-gray-400', icon: '⚪' },
};

export default function ResultsView({ jobId, onBack }: Props) {
  const [results, setResults] = useState<ScanResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedResult, setSelectedResult] = useState<ScanResult | null>(null);
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [sortField, setSortField] = useState<'confidence' | 'table' | 'category'>('confidence');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  const [searchQuery, setSearchQuery] = useState('');
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await api.getScanResults(jobId);
        setResults(data.results);
      } catch {
        // Handle error
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [jobId]);

  const categories = useMemo(() => {
    const cats = new Set(results.map(r => r.category));
    return ['all', ...Array.from(cats)];
  }, [results]);

  const filteredResults = useMemo(() => {
    let filtered = results;

    if (filterCategory !== 'all') {
      filtered = filtered.filter(r => r.category === filterCategory);
    }

    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      filtered = filtered.filter(
        r => r.table.toLowerCase().includes(q) ||
             r.column.toLowerCase().includes(q) ||
             r.subtype.toLowerCase().includes(q)
      );
    }

    filtered.sort((a, b) => {
      let cmp = 0;
      if (sortField === 'confidence') cmp = a.confidence - b.confidence;
      else if (sortField === 'table') cmp = a.table.localeCompare(b.table);
      else if (sortField === 'category') cmp = a.category.localeCompare(b.category);
      return sortDir === 'desc' ? -cmp : cmp;
    });

    return filtered;
  }, [results, filterCategory, searchQuery, sortField, sortDir]);

  const stats = useMemo(() => {
    const byCategory: Record<string, number> = {};
    results.forEach(r => {
      byCategory[r.category] = (byCategory[r.category] || 0) + 1;
    });
    return byCategory;
  }, [results]);

  const handleSort = (field: typeof sortField) => {
    if (sortField === field) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortField(field); setSortDir('desc'); }
  };

  const handleExport = async (format: 'json' | 'csv') => {
    setExporting(true);
    try {
      const data = await api.exportResults(jobId, format);
      const content = format === 'csv' ? data : JSON.stringify(data, null, 2);
      const blob = new Blob([content as string], {
        type: format === 'csv' ? 'text/csv' : 'application/json'
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `scan_${jobId.slice(0, 8)}.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      // Handle error
    } finally {
      setExporting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="animate-slide-up">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-white">Classification Results</h2>
          <p className="text-gray-400 mt-1">
            {results.length} fields classified • Job {jobId.slice(0, 8)}...
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => handleExport('json')} disabled={exporting} className="btn-secondary text-sm flex items-center gap-1.5">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
            </svg>
            JSON
          </button>
          <button onClick={() => handleExport('csv')} disabled={exporting} className="btn-secondary text-sm flex items-center gap-1.5">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
            </svg>
            CSV
          </button>
          <button onClick={onBack} className="btn-secondary text-sm">← Back</button>
        </div>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        {Object.entries(CATEGORY_CONFIG).map(([cat, cfg]) => (
          <div key={cat} className="glass-card-light p-4 cursor-pointer hover:bg-gray-800/40 transition-all"
               onClick={() => setFilterCategory(filterCategory === cat ? 'all' : cat)}>
            <div className="flex items-center gap-2 mb-2">
              <span>{cfg.icon}</span>
              <span className={`text-xs font-medium ${cfg.color}`}>{cat}</span>
            </div>
            <div className="text-2xl font-bold text-white">{stats[cat] || 0}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 mb-4">
        <div className="relative flex-1 max-w-sm">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
          </svg>
          <input
            type="text"
            placeholder="Search tables, columns, subtypes..."
            className="input-field pl-10 py-2 text-sm"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <div className="flex items-center gap-1">
          {categories.map(cat => (
            <button
              key={cat}
              onClick={() => setFilterCategory(cat)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                filterCategory === cat
                  ? 'bg-brand-600/20 text-brand-400 border border-brand-500/30'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
              }`}
            >
              {cat === 'all' ? 'All' : cat.split(' ')[0]}
            </button>
          ))}
        </div>
      </div>

      {/* Results table */}
      <div className="glass-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-800/50">
                {[
                  { key: 'table' as const, label: 'Table' },
                  { key: 'table' as const, label: 'Column' },
                  { key: 'category' as const, label: 'Subtype' },
                  { key: 'category' as const, label: 'Category' },
                  { key: 'confidence' as const, label: 'Confidence' },
                  { key: 'table' as const, label: 'Matched By' },
                ].map((col, i) => (
                  <th
                    key={i}
                    className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider cursor-pointer hover:text-gray-200 transition-colors"
                    onClick={() => handleSort(col.key)}
                  >
                    {col.label}
                    {sortField === col.key && (
                      <span className="ml-1">{sortDir === 'desc' ? '↓' : '↑'}</span>
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/30">
              {filteredResults.map((r, i) => {
                const cfg = CATEGORY_CONFIG[r.category] || CATEGORY_CONFIG['Non-Sensitive'];
                return (
                  <tr
                    key={i}
                    className="hover:bg-gray-800/20 cursor-pointer transition-colors"
                    onClick={() => setSelectedResult(r)}
                  >
                    <td className="px-4 py-3 text-sm text-gray-300 font-mono">{r.table}</td>
                    <td className="px-4 py-3 text-sm text-white font-medium font-mono">{r.column}</td>
                    <td className="px-4 py-3 text-sm">
                      <span className={cfg.color}>{r.subtype}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`badge ${cfg.badge}`}>
                        {cfg.icon} {r.category}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              r.confidence >= 0.75 ? 'bg-emerald-500' :
                              r.confidence >= 0.5 ? 'bg-yellow-500' :
                              r.confidence >= 0.25 ? 'bg-orange-500' : 'bg-gray-600'
                            }`}
                            style={{ width: `${r.confidence * 100}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-400 font-mono">
                          {(r.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-1">
                        {r.matched_by.map(engine => (
                          <span key={engine} className="px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase bg-gray-800 text-gray-400">
                            {engine}
                          </span>
                        ))}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {filteredResults.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            No results match the current filters
          </div>
        )}
      </div>

      {/* Detail drawer */}
      {selectedResult && (
        <FieldDetail
          result={selectedResult}
          onClose={() => setSelectedResult(null)}
        />
      )}
    </div>
  );
}
