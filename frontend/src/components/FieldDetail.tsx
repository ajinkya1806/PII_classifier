import type { ScanResult } from '../api';

interface Props {
  result: ScanResult;
  onClose: () => void;
}

const ENGINE_ICONS: Record<string, { icon: string; label: string }> = {
  rule: { icon: '📝', label: 'Rule Engine' },
  pattern: { icon: '🔍', label: 'Pattern Engine' },
  llm: { icon: '🤖', label: 'LLM (Llama 3.1)' },
};

export default function FieldDetail({ result, onClose }: Props) {
  const engines = [
    {
      key: 'rule',
      ...ENGINE_ICONS.rule,
      fired: result.matched_by.includes('rule'),
      confidence: result.rule_confidence ?? 0,
    },
    {
      key: 'pattern',
      ...ENGINE_ICONS.pattern,
      fired: result.matched_by.includes('pattern'),
      confidence: result.pattern_confidence ?? 0,
    },
    {
      key: 'llm',
      ...ENGINE_ICONS.llm,
      fired: result.matched_by.includes('llm'),
      confidence: result.llm_confidence ?? 0,
    },
  ];

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 animate-fade-in"
        onClick={onClose}
      />

      {/* Drawer */}
      <div className="fixed right-0 top-0 bottom-0 w-full max-w-md bg-gray-900 border-l border-gray-800/50 z-50 overflow-y-auto animate-slide-in shadow-2xl">
        {/* Header */}
        <div className="sticky top-0 bg-gray-900/95 backdrop-blur-xl border-b border-gray-800/50 px-6 py-4 flex items-center justify-between">
          <h3 className="text-lg font-bold text-white">Field Details</h3>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg bg-gray-800 hover:bg-gray-700 flex items-center justify-center transition-colors"
          >
            <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Field identity */}
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 rounded-xl bg-gray-800/40">
                <div className="text-xs text-gray-500 mb-1">Table</div>
                <div className="text-sm font-mono text-white">{result.table}</div>
              </div>
              <div className="p-3 rounded-xl bg-gray-800/40">
                <div className="text-xs text-gray-500 mb-1">Column</div>
                <div className="text-sm font-mono text-white">{result.column}</div>
              </div>
            </div>
          </div>

          {/* Classification */}
          <div className="p-4 rounded-xl bg-gray-800/30 border border-gray-700/30">
            <div className="text-xs text-gray-500 uppercase tracking-wider mb-3">Classification</div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-400">Subtype</span>
                <span className="text-sm font-semibold text-white">{result.subtype}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-400">Category</span>
                <span className={`text-sm font-semibold ${
                  result.category.includes('Financial') ? 'text-red-400' :
                  result.category.includes('Sensitive') ? 'text-orange-400' :
                  result.category === 'PII' ? 'text-yellow-400' :
                  'text-gray-400'
                }`}>{result.category}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-400">Regulation</span>
                <span className="text-sm font-semibold text-brand-400">{result.regulation}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-400">Confidence</span>
                <div className="flex items-center gap-2">
                  <div className="w-24 h-2 bg-gray-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        result.confidence >= 0.75 ? 'bg-emerald-500' :
                        result.confidence >= 0.5 ? 'bg-yellow-500' :
                        result.confidence >= 0.25 ? 'bg-orange-500' : 'bg-gray-600'
                      }`}
                      style={{ width: `${result.confidence * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-bold text-white">
                    {(result.confidence * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Description */}
          <div className="p-3 rounded-xl bg-brand-600/5 border border-brand-600/10">
            <p className="text-sm text-gray-300 italic">{result.description}</p>
          </div>

          {/* Engine breakdown */}
          <div>
            <div className="text-xs text-gray-500 uppercase tracking-wider mb-3">Engine Breakdown</div>
            <div className="space-y-2">
              {engines.map((engine) => (
                <div
                  key={engine.key}
                  className={`p-3 rounded-xl border transition-all ${
                    engine.fired
                      ? 'bg-gray-800/40 border-gray-700/50'
                      : 'bg-gray-800/10 border-gray-800/20 opacity-50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{engine.icon}</span>
                      <span className="text-sm font-medium text-white">{engine.label}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      {engine.fired ? (
                        <span className="badge badge-success">✓ Active</span>
                      ) : (
                        <span className="badge badge-non-sensitive">— Inactive</span>
                      )}
                    </div>
                  </div>
                  {engine.fired && (
                    <div className="mt-2 flex items-center gap-2">
                      <div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-brand-500 rounded-full"
                          style={{ width: `${engine.confidence * 100}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-400 font-mono">
                        {(engine.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* LLM Justification */}
          {result.llm_justification && (
            <div>
              <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">LLM Justification</div>
              <div className="p-3 rounded-xl bg-purple-500/5 border border-purple-500/10">
                <p className="text-sm text-gray-300">{result.llm_justification}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
