import React from 'react';
import { 
  X, 
  ShieldCheck, 
  KeyRound, 
  Building2, 
  Lock, 
  CheckCircle2, 
  Fingerprint, 
  Radio, 
  FileCheck
} from 'lucide-react';
import { ContactProfile } from '../../../types/secure-channel';

interface ContactCredentialsModalProps {
  contact: ContactProfile | null;
  isOpen: boolean;
  onClose: () => void;
  onStartDirectChat?: (contact: ContactProfile) => void;
}

export const ContactCredentialsModal: React.FC<ContactCredentialsModalProps> = ({
  contact,
  isOpen,
  onClose,
  onStartDirectChat,
}) => {
  if (!isOpen || !contact) return null;

  const creds = contact.credentials || {
    clearanceLevel: 'Nivel 3 — Operativo Confidencial',
    entity: 'Superintendencia Nacional Aduanera / GovTech',
    ed25519Key: '0x8F9...3B',
    ed25519Status: 'Validada y Activa',
    permissions: [
      'Desencriptación de PII autorizada',
      'Auditoría de Ledger'
    ],
    sessionId: 'sec-992a-fed',
    department: 'División Operativa',
    idNumber: 'ID: 0x8F9...3B'
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm animate-fade-in">
      <div 
        className="relative w-full max-w-md bg-white dark:bg-[#0c121e] border border-neutral-200/90 dark:border-neutral-800 rounded-2xl shadow-2xl overflow-hidden transition-all duration-300"
        role="dialog"
        aria-modal="true"
      >
        {/* Top Header Strip */}
        <div className="px-6 pt-5 pb-4 border-b border-neutral-100 dark:border-neutral-800/80 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 flex items-center justify-center border border-indigo-200/60 dark:border-indigo-800/50">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-neutral-900 dark:text-white leading-tight">
                Perfil y Credenciales del Usuario
              </h3>
              <div className="flex items-center gap-1.5 mt-0.5">
                <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                <span className="text-[11px] font-medium text-emerald-600 dark:text-emerald-400">
                  Credenciales Verificadas por Aduana IA
                </span>
              </div>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-1.5 rounded-lg text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-200 hover:bg-neutral-100 dark:hover:bg-neutral-800/80 transition-colors"
            aria-label="Cerrar modal"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-5 max-h-[75vh] overflow-y-auto">
          {/* Identity Box */}
          <div className="flex flex-col items-center text-center pb-2">
            <div className="relative mb-3">
              <div className="w-20 h-20 rounded-2xl bg-[#141b29] text-indigo-400 font-bold text-2xl flex items-center justify-center border border-indigo-500/30 shadow-md">
                {contact.initials}
              </div>
              <span className={`w-3.5 h-3.5 rounded-full absolute -bottom-1 -right-1 ring-2 ring-white dark:ring-[#0c121e] ${
                contact.isOnline ? 'bg-emerald-500' : 'bg-slate-400'
              }`} />
            </div>
            <h4 className="text-lg font-bold text-neutral-900 dark:text-white">
              {contact.name}
            </h4>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 font-medium border border-indigo-200/50 dark:border-indigo-800/40">
                {contact.role}
              </span>
              <span className="text-xs font-mono text-neutral-500 dark:text-neutral-400">
                {creds.idNumber}
              </span>
            </div>
          </div>

          {/* Section: Credenciales e Institucionales */}
          <div className="space-y-3">
            <div className="flex items-center justify-between text-[11px] font-semibold uppercase tracking-wider text-neutral-400 dark:text-neutral-500">
              <span>Credenciales e Institucionales</span>
              <span className="text-[10px] font-mono text-emerald-600 dark:text-emerald-400 font-medium">
                ● ACTIVO
              </span>
            </div>

            {/* Clearance Card */}
            <div className="p-3.5 rounded-xl bg-neutral-50 dark:bg-[#111827] border border-neutral-200/80 dark:border-neutral-800/80 space-y-1">
              <div className="flex items-center gap-1.5 text-[11px] font-mono text-neutral-500 dark:text-neutral-400">
                <Lock className="w-3 h-3 text-indigo-500" />
                <span>Nivel de Clearance:</span>
              </div>
              <p className="text-xs font-bold text-neutral-900 dark:text-white pl-4">
                {creds.clearanceLevel}
              </p>
            </div>

            {/* Entity / Unit Card */}
            <div className="p-3.5 rounded-xl bg-neutral-50 dark:bg-[#111827] border border-neutral-200/80 dark:border-neutral-800/80 space-y-1">
              <div className="flex items-center gap-1.5 text-[11px] font-mono text-neutral-500 dark:text-neutral-400">
                <Building2 className="w-3 h-3 text-emerald-500" />
                <span>Entidad / Unidad:</span>
              </div>
              <p className="text-xs font-semibold text-neutral-900 dark:text-white pl-4">
                {creds.entity}
              </p>
              {creds.department && (
                <p className="text-[11px] text-neutral-500 dark:text-neutral-400 pl-4">
                  {creds.department}
                </p>
              )}
            </div>

            {/* Ed25519 Cryptographic Signature */}
            <div className="p-3.5 rounded-xl bg-neutral-50 dark:bg-[#111827] border border-neutral-200/80 dark:border-neutral-800/80 space-y-1">
              <div className="flex items-center justify-between text-[11px] font-mono text-neutral-500 dark:text-neutral-400">
                <div className="flex items-center gap-1.5">
                  <KeyRound className="w-3 h-3 text-amber-500" />
                  <span>Firma Criptográfica Ed25519:</span>
                </div>
                <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold">
                  {creds.ed25519Status}
                </span>
              </div>
              <p className="text-xs font-mono font-medium text-neutral-800 dark:text-neutral-200 pl-4">
                Clave Pública: {creds.ed25519Key}
              </p>
            </div>

            {/* Access Permissions */}
            <div className="p-3.5 rounded-xl bg-neutral-50 dark:bg-[#111827] border border-neutral-200/80 dark:border-neutral-800/80 space-y-1.5">
              <div className="flex items-center gap-1.5 text-[11px] font-mono text-neutral-500 dark:text-neutral-400">
                <FileCheck className="w-3 h-3 text-primary" />
                <span>Permisos de Acceso:</span>
              </div>
              <ul className="space-y-1 pl-4">
                {creds.permissions.map((perm, idx) => (
                  <li key={idx} className="text-xs text-neutral-700 dark:text-neutral-300 flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 shrink-0" />
                    <span>{perm}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Institutional Footer Strip */}
          <div className="p-3 rounded-xl bg-indigo-50/60 dark:bg-indigo-950/20 border border-indigo-200/50 dark:border-indigo-800/40 text-center space-y-1">
            <p className="text-[10px] font-mono text-indigo-700 dark:text-indigo-300 font-semibold tracking-wider uppercase">
              Canal Soberano Segregado • Protocolo Zero-Trust
            </p>
            <p className="text-[10px] font-mono text-neutral-400">
              Sesión Segura ID: {creds.sessionId}
            </p>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-4 bg-neutral-50/90 dark:bg-[#111827]/90 border-t border-neutral-100 dark:border-neutral-800 flex items-center justify-between gap-3">
          <button
            onClick={onClose}
            className="flex-1 py-2 px-3 rounded-xl text-xs font-medium text-neutral-700 dark:text-neutral-300 hover:bg-neutral-200/60 dark:hover:bg-neutral-800 transition-colors"
          >
            Cerrar
          </button>
          {onStartDirectChat && (
            <button
              onClick={() => {
                onStartDirectChat(contact);
                onClose();
              }}
              className="flex-1 py-2 px-3 rounded-xl text-xs font-semibold bg-primary hover:bg-indigo-700 text-white shadow-sm transition-all active:scale-95 flex items-center justify-center gap-1.5"
            >
              <Radio className="w-3.5 h-3.5" />
              <span>Abrir Canal Cifrado</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
