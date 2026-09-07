import { useState } from 'react';
import { api } from '../api';
import type { ConnectionInfo, SchemaTable } from '../api';

interface Props {
  connection: ConnectionInfo;
  schema: SchemaTable[];
  onScanStart: (jobId: string, tables: string[]) => void;
}

export default function SchemaBrowser({ connection, schema, onScanStart }: Props) {
  const [selected, setSelected] = useState<Set<string>>(
    new Set(schema.map((t) => t.table_name))
  );
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggleTable = (name: string) => {
    const next = new Set(selected);
    if (next.has(name)) next.delete(name);
    else next.add(name);
    setSelected(next);
  };

  const toggleExpand = (name: string) => {
    const next = new Set(expanded);
    if (next.has(name)) next.delete(name);
    else next.add(name);
    setExpanded(next);
  };

  const selectAll = () => setSelected(new Set(schema.map((t) => t.table_name)));
  const selectNone = () => setSelected(new Set());

  const startScan = async () => {
    if (selected.size === 0) return;
    setScanning(true);
    setError(null);
    try {
      const tables = Array.from(selected);
      const result = await api.startScan({ ...connection, tables });
      onScanStart(result.job_id, tables);
    } catch (err: any) {
      setError(err.message || 'Failed to start scan');
      setScanning(false);
    }
  };

  const totalColumns = schema
    .filter((t) => selected.has(t.table_name))
    .reduce((sum, t) => sum + t.columns.length, 0);

  return (
    <div className="max-w-4xl mx-auto animate-slide-up">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-white">Schema Browser</h2>
          <p className="text-gray-400 mt-1">
            Connected to <span className="text-brand-400 font-medium">{connection.database}</span> • {schema.length} tables found
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={selectAll} className="text-sm text-brand-400 hover:text-brand-300 transition-colors">
            Select All
          </button>
          <span className="text-gray-600">|</span>
          <button onClick={selectNone} className="text-sm text-gray-400 hover:text-gray-300 transition-colors">
            Select None
          </button>
        </div>
      </div>

      <div className="glass-card divide-y divide-gray-800/50 mb-6 max-h-[60vh] overflow-y-auto">
        {schema.map((table) => (
          <div key={table.table_name} className="group">
            <div className="flex items-center gap-3 px-5 py-3.5 hover:bg-gray-800/30 transition-colors">
              {/* Checkbox */}
              <button
                onClick={() => toggleTable(table.table_name)}
                className={`w-5 h-5 rounded-md border-2 flex items-center justify-center transition-all ${
                  selected.has(table.table_name)
                    ? 'bg-brand-600 border-brand-500'
                    : 'border-gray-600 hover:border-gray-400'
                }`}
              >
                {selected.has(table.table_name) && (
                  <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                )}
              </button>

              {/* Table info */}
              <button
                onClick={() => toggleExpand(table.table_name)}
                className="flex-1 flex items-center gap-3 text-left"
              >
                <svg className="w-4 h-4 text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.375 19.5h17.25m-17.25 0a1.125 1.125 0 01-1.125-1.125M3.375 19.5h7.5c.621 0 1.125-.504 1.125-1.125m-9.75 0V5.625m0 12.75v-1.5c0-.621.504-1.125 1.125-1.125m18.375 2.625V5.625m0 12.75c0 .621-.504 1.125-1.125 1.125m1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125m0 3.75h-7.5A1.125 1.125 0 0112 18.375m9.75-12.75c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125m19.5 0v1.5c0 .621-.504 1.125-1.125 1.125M2.25 5.625v1.5c0 .621.504 1.125 1.125 1.125m0 0h17.25m-17.25 0h7.5c.621 0 1.125.504 1.125 1.125M3.375 8.25c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125m17.25-3.75h-7.5c-.621 0-1.125.504-1.125 1.125m8.625-1.125c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5m-7.5 0c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125M12 10.875v-1.5m0 1.5c0 .621-.504 1.125-1.125 1.125M12 10.875c0 .621.504 1.125 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125M13.125 12h7.5m-7.5 0c-.621 0-1.125.504-1.125 1.125M20.625 12c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5M12 14.625v-1.5m0 1.5c0 .621-.504 1.125-1.125 1.125M12 14.625c0 .621.504 1.125 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125m0 0v1.5c0 .621-.504 1.125-1.125 1.125" />
                </svg>
                <span className="font-medium text-white">{table.table_name}</span>
                <span className="text-xs text-gray-500">({table.columns.length} columns)</span>

                <svg
                  className={`w-4 h-4 text-gray-500 ml-auto transition-transform duration-200 ${
                    expanded.has(table.table_name) ? 'rotate-180' : ''
                  }`}
                  fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                </svg>
              </button>
            </div>

            {/* Column details */}
            {expanded.has(table.table_name) && (
              <div className="px-5 pb-3 animate-fade-in">
                <div className="ml-8 grid grid-cols-2 gap-1">
                  {table.columns.map((col) => (
                    <div key={col.name} className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm">
                      <span className="w-2 h-2 rounded-full bg-gray-600" />
                      <span className="text-gray-300">{col.name}</span>
                      <span className="text-xs text-gray-600 ml-auto">{col.data_type}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {error && (
        <div className="mb-4 p-3 rounded-xl bg-red-500/10 text-red-400 border border-red-500/20 text-sm animate-fade-in">
          ✗ {error}
        </div>
      )}

      {/* Action bar */}
      <div className="glass-card-light p-4 flex items-center justify-between">
        <div className="text-sm text-gray-400">
          <span className="text-white font-semibold">{selected.size}</span> tables selected •{' '}
          <span className="text-white font-semibold">{totalColumns}</span> columns to scan
        </div>
        <button
          id="btn-run-scan"
          onClick={startScan}
          disabled={scanning || selected.size === 0}
          className="btn-primary flex items-center gap-2"
        >
          {scanning ? (
            <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
            </svg>
          )}
          Run Scan
        </button>
      </div>
    </div>
  );
}
