import React from 'react';
import { ArrowRight, Check } from 'lucide-react';
import { AuditBlock } from '../../../types';

interface LedgerSummaryWidgetProps {
  blocks: AuditBlock[];
  onViewFullLedger?: () => void;
}

export const LedgerSummaryWidget: React.FC<LedgerSummaryWidgetProps> = ({
  blocks,
  onViewFullLedger,
}) => {
  return (
    <section 
      className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200/90 dark:border-slate-800 p-6 shadow-xs transition-colors"
      data-purpose="ledger-audit-trail"
      id="sec-ledger"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div>
          <h3 className="text-base font-bold text-slate-900 dark:text-white">
            Ledger — Auditoría Criptográfica
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Registro inalterable con hashes SHA-256 y Ed25519
          </p>
        </div>

        <span className="px-2.5 py-1 rounded-full text-xs font-semibold font-mono bg-indigo-50 dark:bg-indigo-950/60 text-[#4f46e5] dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800/50">
          Sincronizado
        </span>
      </div>

      {/* Vertical Timeline with Blockchain verification nodes */}
      <div className="relative pl-6 space-y-4 before:absolute before:left-3 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-200 dark:before:bg-slate-800">
        
        {blocks.map((block, idx) => {
          const isCorrupted = block.status === 'corrupted';

          return (
            <div key={idx} className="relative flex items-start space-x-3">
              {/* Timeline node icon */}
              {isCorrupted ? (
                <div className="absolute -left-6 mt-1 w-6 h-6 rounded-full bg-rose-100 dark:bg-rose-950 border-2 border-rose-500 flex items-center justify-center text-[11px] text-rose-600 font-bold shadow-2xs">
                  !
                </div>
              ) : (
                <div className="absolute -left-6 mt-1 w-6 h-6 rounded-full bg-emerald-100 dark:bg-emerald-950 border-2 border-emerald-500 flex items-center justify-center text-[10px] text-emerald-600 font-bold shadow-2xs">
                  <Check className="w-3 h-3 stroke-[3]" />
                </div>
              )}

              {/* Card content */}
              <div 
                className={`flex-1 rounded-2xl p-4 transition-all ${
                  isCorrupted
                    ? 'bg-rose-50/90 dark:bg-rose-950/30 border-2 border-rose-300 dark:border-rose-800/80 shadow-2xs'
                    : 'bg-slate-50 dark:bg-slate-800/70 border border-slate-100 dark:border-slate-700/60'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span 
                      className={`px-2 py-0.5 text-xs font-mono font-bold rounded-md ${
                        isCorrupted 
                          ? 'bg-rose-600 text-white' 
                          : 'bg-white dark:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-600'
                      }`}
                    >
                      {block.blockNumber}
                    </span>
                    <span className={`text-xs font-bold ${isCorrupted ? 'text-rose-800 dark:text-rose-200' : 'text-slate-800 dark:text-slate-100'}`}>
                      {block.title}
                    </span>
                    {!isCorrupted && (
                      <span className="text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-200 dark:border-emerald-800/40">
                        {block.statusLabel}
                      </span>
                    )}
                  </div>

                  <span className={`text-[11px] font-mono ${isCorrupted ? 'text-rose-600 dark:text-rose-400 font-bold' : 'text-slate-400'}`}>
                    {isCorrupted ? block.statusLabel : block.timeRange}
                  </span>
                </div>

                <div className={`text-[11px] font-mono space-y-1 break-all ${isCorrupted ? 'text-rose-700 dark:text-rose-300/90' : 'text-slate-500 dark:text-slate-400'}`}>
                  <p>
                    <span className={`font-semibold ${isCorrupted ? 'text-rose-900 dark:text-rose-200' : 'text-slate-600 dark:text-slate-300'}`}>SHA-256:</span>{' '}
                    <span>{block.sha256Hash}</span>
                  </p>
                  <p>
                    <span className={`font-semibold ${isCorrupted ? 'text-rose-900 dark:text-rose-200' : 'text-slate-600 dark:text-slate-300'}`}>Ed25519:</span>{' '}
                    <span>{block.ed25519Signature}</span>
                  </p>
                </div>
              </div>
            </div>
          );
        })}

      </div>

      {/* Footer Navigation Link */}
      {onViewFullLedger && (
        <div className="mt-5 pt-3 border-t border-slate-100 dark:border-slate-800 flex justify-end">
          <button
            onClick={onViewFullLedger}
            className="text-xs font-semibold text-[#4f46e5] dark:text-indigo-400 hover:underline inline-flex items-center gap-1"
          >
            <span>Ver Registro Completo y Simulación</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}
    </section>
  );
};
