import React from 'react';
import { X, ShieldCheck, CheckCircle2, Lock, Copy } from 'lucide-react';

interface ProofModalProps {
  isOpen: boolean;
  onClose: () => void;
  recordId: string;
  sha256Hash: string;
  onCopy: (text: string) => void;
}

export const ProofModal: React.FC<ProofModalProps> = ({
  isOpen,
  onClose,
  recordId,
  sha256Hash,
  onCopy,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-150">
      <div 
        className="w-full max-w-lg bg-white dark:bg-[#131826] border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-150"
        role="dialog"
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-indigo-50/60 dark:bg-indigo-950/30">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-[#3525cd] text-white">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                Firma Criptográfica Soberana
              </h3>
              <p className="text-xs text-slate-500 font-mono">Certificado de Verificación Ed25519</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4 text-xs">
          <div className="flex items-center justify-between p-3 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/60">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
              <div>
                <p className="font-semibold text-emerald-900 dark:text-emerald-300">
                  Firma Válida & Cadena No Alterada
                </p>
                <p className="text-[11px] text-emerald-700/80 dark:text-emerald-400/80">
                  Sello institucional generado por Nodo Soberano #01
                </p>
              </div>
            </div>
            <span className="font-mono text-[10px] uppercase font-bold text-emerald-800 dark:text-emerald-300 bg-emerald-100 dark:bg-emerald-900/60 px-2 py-0.5 rounded">
              Nivel A+
            </span>
          </div>

          <div className="space-y-3">
            <div>
              <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold block mb-1">
                Expediente Auditado
              </span>
              <div className="font-mono text-slate-800 dark:text-slate-200 font-semibold bg-slate-50 dark:bg-slate-900 p-2.5 rounded-lg border border-slate-200 dark:border-slate-800">
                {recordId}
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold">
                  Hash Canónico SHA-256
                </span>
                <button
                  onClick={() => onCopy(sha256Hash)}
                  className="text-[11px] text-[#3525cd] dark:text-indigo-400 hover:underline flex items-center gap-1 font-mono font-medium"
                >
                  <Copy className="w-3 h-3" /> Copiar Hash
                </button>
              </div>
              <div className="font-mono text-[11px] text-slate-700 dark:text-slate-300 bg-slate-50 dark:bg-slate-900 p-2.5 rounded-lg border border-slate-200 dark:border-slate-800 break-all select-all">
                {sha256Hash}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 pt-1 font-mono text-[11px]">
              <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                <span className="text-slate-400 text-[10px] uppercase block">Clave Pública Custodio</span>
                <span className="text-slate-700 dark:text-slate-300 font-semibold">ED-PUBKEY-9821</span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                <span className="text-slate-400 text-[10px] uppercase block">Timestamp de Sellado</span>
                <span className="text-slate-700 dark:text-slate-300 font-semibold">2025-02-14 14:30:19 UTC</span>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 text-slate-500 text-[11px] leading-relaxed">
              <span className="font-semibold text-slate-700 dark:text-slate-300">Inmutabilidad Garantizada:</span> Esta firma criptográfica no puede ser falsificada sin comprometer el quórum de 8 custodios del Consorcio GovTech.
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-slate-400 text-[11px] font-mono">
            <Lock className="w-3 h-3" /> ISO/IEC 27001 Verified
          </div>
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-semibold text-white bg-[#3525cd] hover:bg-indigo-700 rounded-lg shadow-xs transition-colors"
          >
            Cerrar Certificado
          </button>
        </div>
      </div>
    </div>
  );
};
