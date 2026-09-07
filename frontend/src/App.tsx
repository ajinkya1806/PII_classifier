import { useState } from 'react';
import ConnectionForm from './components/ConnectionForm';
import SchemaBrowser from './components/SchemaBrowser';
import ScanProgress from './components/ScanProgress';
import ResultsView from './components/ResultsView';
import ScanHistory from './components/ScanHistory';
import type { ConnectionInfo, SchemaTable } from './api';

type Screen = 'connect' | 'schema' | 'scanning' | 'results' | 'history';

function App() {
  const [screen, setScreen] = useState<Screen>('connect');
  const [connection, setConnection] = useState<ConnectionInfo | null>(null);
  const [schema, setSchema] = useState<SchemaTable[]>([]);
  const [jobId, setJobId] = useState<string>('');

  const handleConnected = (conn: ConnectionInfo, tables: SchemaTable[]) => {
    setConnection(conn);
    setSchema(tables);
    setScreen('schema');
  };

  const handleScanStart = (id: string, _tables: string[]) => {
    setJobId(id);
    setScreen('scanning');
  };

  const handleScanComplete = () => {
    setScreen('results');
  };

  const handleViewHistoryJob = (id: string) => {
    setJobId(id);
    setScreen('results');
  };

  return (
    <div className="min-h-screen bg-gray-950 relative overflow-hidden">
      {/* Ambient background glow */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-brand-600/5 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-purple-600/5 rounded-full blur-[120px]" />
      </div>

      {/* Header */}
      <header className="relative z-10 border-b border-gray-800/50 bg-gray-950/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center shadow-lg shadow-brand-600/20">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
              </svg>
            </div>
            <div>
              <h1 className="text-lg font-bold text-white tracking-tight">PII Classifier</h1>
              <p className="text-xs text-gray-500">DPDP & RBI-DADP Compliance</p>
            </div>
          </div>

          <nav className="flex items-center gap-1">
            {[
              { key: 'connect', label: 'Connect', icon: '🔌' },
              { key: 'schema', label: 'Schema', icon: '📋' },
              { key: 'history', label: 'History', icon: '📊' },
            ].map((item) => (
              <button
                key={item.key}
                onClick={() => setScreen(item.key as Screen)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  screen === item.key
                    ? 'bg-brand-600/20 text-brand-400'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
                }`}
              >
                <span className="mr-1.5">{item.icon}</span>
                {item.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      {/* Main content */}
      <main className="relative z-10 max-w-7xl mx-auto px-6 py-8 animate-fade-in">
        {screen === 'connect' && (
          <ConnectionForm onConnected={handleConnected} />
        )}
        {screen === 'schema' && connection && (
          <SchemaBrowser
            connection={connection}
            schema={schema}
            onScanStart={handleScanStart}
          />
        )}
        {screen === 'scanning' && (
          <ScanProgress jobId={jobId} onComplete={handleScanComplete} />
        )}
        {screen === 'results' && (
          <ResultsView jobId={jobId} onBack={() => setScreen('schema')} />
        )}
        {screen === 'history' && (
          <ScanHistory onViewJob={handleViewHistoryJob} />
        )}
      </main>
    </div>
  );
}

export default App;
