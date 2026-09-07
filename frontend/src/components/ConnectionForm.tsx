import { useState } from 'react';
import { api } from '../api';
import type { ConnectionInfo, SchemaTable } from '../api';

interface Props {
  onConnected: (conn: ConnectionInfo, schema: SchemaTable[]) => void;
}

export default function ConnectionForm({ onConnected }: Props) {
  const [form, setForm] = useState<ConnectionInfo>({
    host: 'localhost',
    port: 3306,
    user: '',
    password: '',
    database: '',
  });
  const [testing, setTesting] = useState(false);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const handleChange = (field: keyof ConnectionInfo, value: string | number) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    setStatus(null);
  };

  const testConnection = async () => {
    setTesting(true);
    setStatus(null);
    try {
      const result = await api.testConnection(form);
      setStatus({
        type: result.success ? 'success' : 'error',
        message: result.message,
      });
    } catch (err: any) {
      setStatus({ type: 'error', message: err.message || 'Connection failed' });
    } finally {
      setTesting(false);
    }
  };

  const connectAndBrowse = async () => {
    setLoading(true);
    setStatus(null);
    try {
      const schema = await api.getSchema(form);
      onConnected(form, schema);
    } catch (err: any) {
      setStatus({ type: 'error', message: err.message || 'Failed to fetch schema' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-lg mx-auto animate-slide-up">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold bg-gradient-to-r from-brand-400 to-purple-400 bg-clip-text text-transparent">
          Connect to Database
        </h2>
        <p className="text-gray-400 mt-2">Enter your MySQL connection details to begin scanning</p>
      </div>

      <div className="glass-card p-8">
        <div className="space-y-5">
          <div className="grid grid-cols-3 gap-4">
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-400 mb-1.5">Host</label>
              <input
                id="input-host"
                type="text"
                className="input-field"
                value={form.host}
                onChange={(e) => handleChange('host', e.target.value)}
                placeholder="localhost"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1.5">Port</label>
              <input
                id="input-port"
                type="number"
                className="input-field"
                value={form.port}
                onChange={(e) => handleChange('port', parseInt(e.target.value) || 3306)}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1.5">Username</label>
            <input
              id="input-user"
              type="text"
              className="input-field"
              value={form.user}
              onChange={(e) => handleChange('user', e.target.value)}
              placeholder="root"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1.5">Password</label>
            <input
              id="input-password"
              type="password"
              className="input-field"
              value={form.password}
              onChange={(e) => handleChange('password', e.target.value)}
              placeholder="••••••••"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1.5">Database</label>
            <input
              id="input-database"
              type="text"
              className="input-field"
              value={form.database}
              onChange={(e) => handleChange('database', e.target.value)}
              placeholder="my_database"
            />
          </div>

          {/* Status message */}
          {status && (
            <div
              className={`p-3 rounded-xl text-sm animate-fade-in ${
                status.type === 'success'
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                  : 'bg-red-500/10 text-red-400 border border-red-500/20'
              }`}
            >
              {status.type === 'success' ? '✓ ' : '✗ '}{status.message}
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <button
              id="btn-test-connection"
              onClick={testConnection}
              disabled={testing || !form.user || !form.database}
              className="btn-secondary flex-1 flex items-center justify-center gap-2"
            >
              {testing ? (
                <span className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
              ) : (
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              )}
              Test Connection
            </button>
            <button
              id="btn-connect"
              onClick={connectAndBrowse}
              disabled={loading || !form.user || !form.database}
              className="btn-primary flex-1 flex items-center justify-center gap-2"
            >
              {loading ? (
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                </svg>
              )}
              Connect & Browse
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
