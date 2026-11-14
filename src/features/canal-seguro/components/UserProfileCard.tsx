import React from 'react';
import { Check } from 'lucide-react';
import { AuditorUserProfile } from '../../../types';

interface UserProfileCardProps {
  profile: AuditorUserProfile;
}

export const UserProfileCard: React.FC<UserProfileCardProps> = ({ profile }) => {
  return (
    <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-5 shadow-xs h-[650px] flex flex-col justify-between transition-colors">
      <div>
        {/* Header */}
        <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-100 dark:border-slate-800">
          <h3 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider font-mono">
            Perfil del Usuario
          </h3>
          <span className="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-1 font-mono">
            <Check className="w-3 h-3 stroke-[3]" />
            Verificado
          </span>
        </div>

        {/* Big Avatar */}
        <div className="flex flex-col items-center text-center my-4">
          <div className="w-20 h-20 rounded-3xl bg-indigo-100 dark:bg-indigo-950/60 text-[#4f46e5] dark:text-indigo-300 font-extrabold text-2xl flex items-center justify-center shadow-inner mb-3">
            {profile.initials}
          </div>
          <h4 className="font-bold text-sm text-slate-900 dark:text-white">
            {profile.name}
          </h4>
          <p className="text-xs font-mono text-slate-400 mt-0.5">
            {profile.idNumber}
          </p>
        </div>

        {/* Credential Blocks */}
        <div className="space-y-3 mt-4 text-xs font-sans">
          <div className="p-3 bg-slate-50 dark:bg-slate-800/80 rounded-xl border border-slate-100 dark:border-slate-700/60">
            <span className="text-[10px] uppercase font-bold text-slate-400 block mb-0.5 font-mono">
              Nivel de Clearance:
            </span>
            <p className="font-bold text-slate-800 dark:text-slate-100">
              {profile.clearanceLevel}
            </p>
          </div>

          <div className="p-3 bg-slate-50 dark:bg-slate-800/80 rounded-xl border border-slate-100 dark:border-slate-700/60">
            <span className="text-[10px] uppercase font-bold text-slate-400 block mb-0.5 font-mono">
              Entidad / Unidad:
            </span>
            <p className="font-bold text-slate-800 dark:text-slate-100">
              {profile.department}
            </p>
          </div>

          <div className="p-3 bg-slate-50 dark:bg-slate-800/80 rounded-xl border border-slate-100 dark:border-slate-700/60">
            <span className="text-[10px] uppercase font-bold text-slate-400 block mb-0.5 font-mono">
              Firma Criptográfica Ed25519:
            </span>
            <p className="font-semibold text-emerald-600 dark:text-emerald-400 font-mono">
              {profile.ed25519Status}
            </p>
          </div>
        </div>
      </div>

      {/* Bottom Access Capabilities */}
      <div className="p-3 bg-indigo-50/50 dark:bg-indigo-950/30 rounded-xl border border-indigo-100 dark:border-indigo-900/40 text-[11px] text-slate-600 dark:text-slate-300">
        <span className="font-bold text-[#4f46e5] dark:text-indigo-300 block mb-1">
          Permisos de Acceso:
        </span>
        {profile.permissionsSummary}
      </div>
    </div>
  );
};
