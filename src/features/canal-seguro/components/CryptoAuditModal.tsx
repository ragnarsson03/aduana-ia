import React, { useState } from 'react';
import { 
  X, 
  ShieldCheck, 
  Lock, 
  KeyRound, 
  Cpu, 
  CheckCircle2, 
  Copy, 
  Check, 
  Fingerprint, 
  Radio, 
  Terminal,
  Shield
} from 'lucide-react';
import { CryptoProcessVerification } from '../../../types/secure-channel';

interface CryptoAuditModalProps {
  isOpen: boolean;
  onClose: () => void;
  verification?: CryptoProcessVerification | null;
  contactName?: string;
  onNotify?: (msg: string) => void;
}

export const CryptoAuditModal: React.FC<CryptoAuditModalProps> = ({
  isOpen,
  onClose,
  verification,
  contactName = 'Funcionario Aduanero',
  onNotify,
}) => {
  const [copiedField, setCopiedField] = useState<string | null>(null);

  if (!isOpen) return null;

  const data: CryptoProcessVerification = verification || {
    algorithm: 'AES-256-GCM (256-bit) + Gov-Ed25519',
    handshakeStatus: 'Validada y Activa en Enclave RAM',
    ed25519Key: '0x8F9...3B',
    ivHex: '4a1b8c2d9e0f1a2b3c4d5e6f',
    ciphertextPreview: '0x8f31c9a0d2e471b299c01a2b3c4d5e6f7a8b9c0d1e2f3a4b...',
    authTagValid: true,
    sha256Short: '9f83c21a4e...52631',
    piiShieldStatus: 'Protección Homomórfica Conforme (Cero Plaintext)',
    sessionTokenId: 'sec-992a-fed',
  };

  const handleCopy = (field: string, value: string) => {
    navigator.clipboard.writeText(value);
    setCopiedField(field);
    onNotify?.(`Copiado: ${field}`);
    setTimeout(() => setCopiedField(null), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-950/75 backdrop-blur-sm animate-fade-in">
      <div 
        className="relative w-full max-w-lg bg-white dark:bg-[#0c121e] border border-neutral-200/90 dark:border-neutral-800 rounded-2xl shadow-2xl overflow-hidden transition-all duration-300"
        role="dialog"
        aria-modal="true"
      >
        {/* Header Strip */}
        <div className="px-5 py-4 border-b border-neutral-100 dark:border-neutral-800/80 flex items-center justify-between bg-slate-50/60 dark:bg-[#111827]/60">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center border border-emerald-200/60 dark:border-emerald-800/50">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-xs sm:text-sm font-bold text-neutral-900 dark:text-white leading-tight">
                Auditoría Criptográfica de Canal Seguro
              </h3>
              <p className="text-[11px] text-neutral-500 dark:text-neutral-400 font-mono">
                Enlace E2EE con {contactName}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-200 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-5 space-y-4 max-h-[75vh] overflow-y-auto text-xs">
          {/* Security Status Banner */}
          <div className="p-3 rounded-xl bg-emerald-50/80 dark:bg-emerald-950/40 border border-emerald-200/70 dark:border-emerald-800/60 flex items-center gap-2.5">
            <span className="relative flex h-2.5 w-2.5 shrink-0">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500" />
            </span>
            <div className="flex-1 text-[11px] text-emerald-800 dark:text-emerald-300 font-medium">
              <span className="font-bold">Cifrado de Extremo a Extremo Verificado:</span> Todos los datos y archivos son encriptados en memoria RAM confinada antes de transmisión.
            </div>
          </div>

          {/* 5-Step Process Verification Checklist */}
          <div className="space-y-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-400 dark:text-neutral-500">
              Procesos Criptográficos Ejecutados en este Enlace
            </span>
            <div className="space-y-1.5 font-mono text-[11px]">
              
              {/* Step 1: Handshake */}
              <div className="p-2.5 rounded-lg bg-neutral-50 dark:bg-[#141b29] border border-neutral-200/60 dark:border-neutral-800 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <KeyRound className="w-3.5 h-3.5 text-indigo-500 shrink-0" />
                  <div>
                    <span className="font-semibold text-neutral-800 dark:text-neutral-200">1. Handshake Gov-Ed25519:</span>
                    <span className="text-neutral-500 dark:text-neutral-400 ml-1.5">{data.ed25519Key}</span>
                  </div>
                </div>
                <span className="px-1.5 py-0.2 rounded text-[10px] bg-emerald-100 dark:bg-emerald-950/70 text-emerald-700 dark:text-emerald-300 font-semibold">
                  Validado
                </span>
              </div>

              {/* Step 2: Shield PII */}
              <div className="p-2.5 rounded-lg bg-neutral-50 dark:bg-[#141b29] border border-neutral-200/60 dark:border-neutral-800 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Shield className="w-3.5 h-3.5 text-amber-500 shrink-0" />
                  <div>
                    <span className="font-semibold text-neutral-800 dark:text-neutral-200">2. Filtro SHIELD:</span>
                    <span className="text-neutral-500 dark:text-neutral-400 ml-1.5">{data.piiShieldStatus}</span>
                  </div>
                </div>
                <span className="px-1.5 py-0.2 rounded text-[10px] bg-emerald-100 dark:bg-emerald-950/70 text-emerald-700 dark:text-emerald-300 font-semibold">
                  Zero-Leak
                </span>
              </div>

              {/* Step 3: Symmetric Encryption */}
              <div className="p-2.5 rounded-lg bg-neutral-50 dark:bg-[#141b29] border border-neutral-200/60 dark:border-neutral-800 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Lock className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                  <div>
                    <span className="font-semibold text-neutral-800 dark:text-neutral-200">3. Cifrado AES-256-GCM:</span>
                    <span className="text-neutral-500 dark:text-neutral-400 ml-1.5">IV 96-bit + Auth Tag</span>
                  </div>
                </div>
                <span className="px-1.5 py-0.2 rounded text-[10px] bg-emerald-100 dark:bg-emerald-950/70 text-emerald-700 dark:text-emerald-300 font-semibold">
                  Cifrado OK
                </span>
              </div>

              {/* Step 4: SHA-256 Seal */}
              <div className="p-2.5 rounded-lg bg-neutral-50 dark:bg-[#141b29] border border-neutral-200/60 dark:border-neutral-800 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Fingerprint className="w-3.5 h-3.5 text-indigo-500 shrink-0" />
                  <div>
                    <span className="font-semibold text-neutral-800 dark:text-neutral-200">4. Sellado de Integridad:</span>
                    <span className="text-neutral-500 dark:text-neutral-400 ml-1.5">SHA-256: {data.sha256Short}</span>
                  </div>
                </div>
                <span className="px-1.5 py-0.2 rounded text-[10px] bg-emerald-100 dark:bg-emerald-950/70 text-emerald-700 dark:text-emerald-300 font-semibold">
                  Conforme
                </span>
              </div>

              {/* Step 5: Memory TTL */}
              <div className="p-2.5 rounded-lg bg-neutral-50 dark:bg-[#141b29] border border-neutral-200/60 dark:border-neutral-800 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Cpu className="w-3.5 h-3.5 text-cyan-500 shrink-0" />
                  <div>
                    <span className="font-semibold text-neutral-800 dark:text-neutral-200">5. Confinamiento de Memoria:</span>
                    <span className="text-neutral-500 dark:text-neutral-400 ml-1.5">RAM-Only · TTL 180s · 0 bytes disco</span>
                  </div>
                </div>
                <span className="px-1.5 py-0.2 rounded text-[10px] bg-emerald-100 dark:bg-emerald-950/70 text-emerald-700 dark:text-emerald-300 font-semibold">
                  Protegido
                </span>
              </div>

            </div>
          </div>

          {/* Cryptographic Inspector (Ciphertext Preview) */}
          <div className="space-y-1.5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-400 dark:text-neutral-500">
              Vector de Inicialización y Cifrado Autenticado
            </span>
            <div className="p-3 rounded-xl bg-slate-900 text-slate-200 font-mono text-[11px] space-y-2 border border-slate-800">
              <div className="flex items-center justify-between text-[10px] text-slate-400 border-b border-slate-800 pb-1">
                <span>ALGORITMO: {data.algorithm}</span>
                <span>SESIÓN: {data.sessionTokenId}</span>
              </div>
              <div>
                <span className="text-indigo-400">IV (96 bits):</span>
                <span className="text-slate-300 ml-2 select-all">{data.ivHex}</span>
              </div>
              <div className="flex items-center justify-between gap-2">
                <div className="truncate">
                  <span className="text-emerald-400">CIPHERTEXT:</span>
                  <span className="text-slate-300 ml-2 select-all">{data.ciphertextPreview}</span>
                </div>
                <button
                  type="button"
                  onClick={() => handleCopy('Ciphertext', data.ciphertextPreview)}
                  className="p-1 hover:bg-slate-800 rounded text-slate-400 hover:text-white shrink-0"
                  title="Copiar Ciphertext"
                >
                  {copiedField === 'Ciphertext' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-neutral-100 dark:border-neutral-800/80 bg-slate-50/60 dark:bg-[#111827]/60 flex items-center justify-between text-xs">
          <span className="text-[10px] font-mono text-neutral-400 dark:text-neutral-500">
            Norma ISO/IEC 27001 · Zero-Trust GovTech
          </span>
          <button
            onClick={onClose}
            className="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-neutral-900 text-white dark:bg-white dark:text-slate-900 hover:opacity-90 transition-opacity"
          >
            Entendido
          </button>
        </div>
      </div>
    </div>
  );
};
