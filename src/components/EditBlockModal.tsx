import React, { useState, useEffect } from 'react';
import { X, AlertTriangle, RefreshCw, CheckCircle2 } from 'lucide-react';

interface EditBlockModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSaveTampered: (newPayload: string, newHash: string) => void;
  onRestore: () => void;
  initialPayload: string;
}

export const EditBlockModal: React.FC<EditBlockModalProps> = ({
  isOpen,
  onClose,
  onSaveTampered,
  onRestore,
  initialPayload,
}) => {
  const [payload, setPayload] = useState(initialPayload);
  const [calculatedHash, setCalculatedHash] = useState('');
  const [isCalculating, setIsCalculating] = useState(false);

  // Compute SHA-256 hash of the payload in real-time
  useEffect(() => {
    let isCurrent = true;
    const computeHash = async () => {
      setIsCalculating(true);
      try {
        const encoder = new TextEncoder();
        const data = encoder.encode(payload);
        const hashBuffer = await crypto.subtle.digest('SHA-256', data);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const hashHex = '0x' + hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
        if (isCurrent) {
          setCalculatedHash(hashHex);
        }
      } catch (e) {
        if (isCurrent) setCalculatedHash('0xff4a12ec7009da331908bf...');
      } finally {
        if (isCurrent) setIsCalculating(false);
      }
    };
    computeHash();
    return () => { isCurrent = false; };
  }, [payload]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-150">
      <div 
        className="w-full max-w-xl bg-white dark:bg-[#131826] border border-slate-200 dark:border-slate-800 rounded-2xl shadow-xl overflow-hidden animate-in zoom-in-95 duration-150"
        role="dialog"
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-900/50">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-lg bg-amber-50 dark:bg-amber-950/60 text-amber-600 dark:text-amber-400">
              <AlertTriangle className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                Simulador de Sabotaje / Alteración de Bloque
              </h3>
              <p className="text-xs text-slate-500 font-mono">Bloque #004 · Auditoría Forense</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-4">
          <div>
            <label className="block text-xs font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400 font-semibold mb-1.5">
              Cuerpo Transaccional del Bloque (Payload)
            </label>
            <textarea
              rows={3}
              value={payload}
              onChange={(e) => setPayload(e.target.value)}
              className="w-full text-xs font-mono p-3 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 focus:outline-hidden focus:ring-2 focus:ring-[#3525cd] transition-all"
              placeholder="Modifica el texto para simular una inyección de parámetros..."
            />
            <p className="text-[11px] text-slate-500 mt-1">
              Prueba cambiando el porcentaje de subsidio o agregando un carácter.
            </p>
          </div>

          <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold">
                Hash SHA-256 Resultante
              </span>
              {isCalculating && (
                <span className="text-[10px] font-mono text-indigo-500 flex items-center gap-1">
                  <RefreshCw className="w-2.5 h-2.5 animate-spin" /> recalculando
                </span>
              )}
            </div>
            <div className="font-mono text-xs text-red-600 dark:text-red-400 break-all select-all font-medium">
              {calculatedHash || 'Calculando...'}
            </div>
          </div>

          <div className="text-xs text-slate-600 dark:text-slate-300 bg-amber-50/80 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800/60 p-3 rounded-lg">
            <strong>Efecto en la Cadena:</strong> Al mutar este bloque sin poseer la clave privada del quórum soberano, el hash ya no concuerda con el cálculo en memoria, aislando el nodo de inmediato.
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 border-t border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 flex flex-col sm:flex-row items-center justify-between gap-2">
          <button
            onClick={() => {
              onRestore();
              onClose();
            }}
            className="w-full sm:w-auto px-3.5 py-1.5 text-xs font-medium text-emerald-700 dark:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-950/40 rounded-lg transition-colors flex items-center justify-center gap-1.5"
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            Restaurar a Estado Válido
          </button>

          <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
            <button
              onClick={onClose}
              className="px-3.5 py-1.5 text-xs font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-800 rounded-lg transition-colors"
            >
              Cancelar
            </button>
            <button
              onClick={() => {
                onSaveTampered(payload, calculatedHash);
                onClose();
              }}
              className="px-4 py-1.5 text-xs font-semibold text-white bg-[#ba1a1a] hover:bg-red-700 rounded-lg shadow-xs transition-colors"
            >
              Aplicar Alteración
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
