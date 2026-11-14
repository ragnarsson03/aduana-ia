import React from 'react';

interface IncomingPromptCardProps {
  onTokenClick?: (token: string) => void;
}

export const IncomingPromptCard: React.FC<IncomingPromptCardProps> = ({ onTokenClick }) => {
  return (
    <div className="flex flex-col justify-between p-4 bg-white/95 dark:bg-slate-800/90 backdrop-blur-xs border border-slate-200 dark:border-slate-700/80 rounded-2xl shadow-xs transition-colors">
      <div>
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs uppercase tracking-wider font-bold text-slate-400 dark:text-slate-500">
            Petición Entrante
          </span>
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 dark:bg-amber-950/50 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800/50">
            Sanitizado
          </span>
        </div>

        <p className="text-xs text-slate-500 dark:text-slate-400 mb-1 font-medium">
          Ciudadano:
        </p>

        <div className="text-xs leading-relaxed font-mono bg-slate-50 dark:bg-slate-900/60 p-3 rounded-xl border border-slate-100 dark:border-slate-800 text-slate-700 dark:text-slate-300">
          "Ciudadano, solicito información sobre beca de estudios{' '}
          <span 
            onClick={() => onTokenClick?.('[CÉDULA_OCULTA]')}
            className="cursor-pointer bg-indigo-100 text-indigo-800 dark:bg-indigo-900/60 dark:text-indigo-300 px-1 py-0.5 rounded text-[11px] font-semibold hover:bg-indigo-200 dark:hover:bg-indigo-800 transition-colors"
          >
            [CÉDULA_OCULTA]
          </span>{' '}
          <span 
            onClick={() => onTokenClick?.('[TELÉFONO_OCULTO]')}
            className="cursor-pointer bg-indigo-100 text-indigo-800 dark:bg-indigo-900/60 dark:text-indigo-300 px-1 py-0.5 rounded text-[11px] font-semibold hover:bg-indigo-200 dark:hover:bg-indigo-800 transition-colors"
          >
            [TELÉFONO_OCULTO]
          </span>{' '}
          contacto{' '}
          <span className="underline decoration-indigo-400 font-semibold">
            @correo.ve
          </span>{' '}
          vinculada a mi registro."
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-700/50 flex items-center justify-between text-[11px] text-slate-500 font-mono">
        <span>Token Shield V2</span>
        <span className="text-emerald-600 dark:text-emerald-400 font-semibold">
          PII Ofuscado
        </span>
      </div>
    </div>
  );
};
