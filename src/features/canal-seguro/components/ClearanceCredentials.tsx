import React from 'react';
import { Check } from 'lucide-react';
import { AuditorUserProfile } from '../../../types';

interface ClearanceCredentialsProps {
  profile: AuditorUserProfile;
}

export const ClearanceCredentials: React.FC<ClearanceCredentialsProps> = ({ profile }) => {
  return (
    <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200/90 dark:border-slate-800 p-5 shadow-xs h-[650px] flex flex-col justify-between transition-colors">
      <div>
        
        {/* Header */}
        <div className="pb-3 border-b border-slate-100 dark:border-slate-800">
          <h3 className="text-sm font-bold text-slate-900 dark:text-white leading-tight">
            Perfil y Credenciales del Usuario
          </h3>
          <p className="text-[11px] font-medium text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5 mt-1">
            <Check className="w-3.5 h-3.5 stroke-[2.5]" />
            <span>{profile.verifiedBadgeText || 'Credenciales Verificadas por Aduana IA'}</span>
          </p>
        </div>

        {/* Big Avatar & Identity */}
        <div className="flex flex-col items-center text-center my-6">
          <div className="w-20 h-20 rounded-2xl bg-indigo-100/80 dark:bg-indigo-950/70 text-[#4f46e5] dark:text-indigo-300 font-black text-2xl flex items-center justify-center shadow-inner mb-3 select-none">
            {profile.initials}
          </div>
          <h4 className="font-bold text-sm text-slate-900 dark:text-white">
            {profile.name}
          </h4>
          <p className="text-xs font-mono text-slate-400 dark:text-slate-500 mt-0.5">
            {profile.idNumber}
          </p>
        </div>

        {/* Section Title */}
        <p className="text-xs font-bold text-slate-700 dark:text-slate-300 mb-3 px-0.5">
          Credenciales e Institucionales
        </p>

        {/* 4 Stacked Credential Cards */}
        <div className="space-y-2.5 text-xs">
          
          {/* Card 1: Clearance */}
          <div className="p-3 bg-slate-50/70 dark:bg-slate-800/70 rounded-xl border border-slate-100 dark:border-slate-700/60">
            <span className="text-[10px] text-slate-400 dark:text-slate-500 font-mono block mb-0.5">
              Nivel de Clearance:
            </span>
            <p className="font-bold text-slate-800 dark:text-slate-100">
              {profile.clearanceLevel}
            </p>
          </div>

          {/* Card 2: Entity / Unit */}
          <div className="p-3 bg-slate-50/70 dark:bg-slate-800/70 rounded-xl border border-slate-100 dark:border-slate-700/60">
            <span className="text-[10px] text-slate-400 dark:text-slate-500 font-mono block mb-0.5">
              Entidad / Unidad:
            </span>
            <p className="font-bold text-slate-800 dark:text-slate-100">
              {profile.department}
            </p>
          </div>

          {/* Card 3: Cryptographic signature */}
          <div className="p-3 bg-slate-50/70 dark:bg-slate-800/70 rounded-xl border border-slate-100 dark:border-slate-700/60">
            <span className="text-[10px] text-slate-400 dark:text-slate-500 font-mono block mb-0.5">
              Firma Criptográfica Ed25519:
            </span>
            <p className="font-semibold text-slate-800 dark:text-slate-100 font-mono">
              {profile.ed25519Status}
            </p>
          </div>

          {/* Card 4: Access permissions */}
          <div className="p-3 bg-slate-50/70 dark:bg-slate-800/70 rounded-xl border border-slate-100 dark:border-slate-700/60">
            <span className="text-[10px] text-slate-400 dark:text-slate-500 font-mono block mb-0.5">
              Permisos de Acceso:
            </span>
            <p className="font-medium text-slate-700 dark:text-slate-300 leading-snug">
              {profile.permissionsSummary}
            </p>
          </div>

        </div>

      </div>

      <div className="text-[10px] text-slate-400 font-mono text-center pt-2">
        Canal Soberano Segregado • Protocolo Zero-Trust
      </div>
    </div>
  );
};
