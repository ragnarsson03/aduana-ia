import React from 'react';
import { Shield, Lock } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="w-full border-t border-slate-200/80 dark:border-slate-800/80 bg-white dark:bg-[#0c101d] py-3.5 px-4 sm:px-6 lg:px-8 mt-6 sm:mt-8 transition-colors">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400">
          <Shield className="w-3.5 h-3.5 text-[#4f46e5] dark:text-indigo-400 shrink-0" />
          <span className="font-medium">
            Aduana IA — Supervisión Algorítmica Soberana y Ciberseguridad GovTech
          </span>
        </div>
        <div className="flex items-center gap-2 font-mono text-[11px] text-slate-400 dark:text-slate-500">
          <Lock className="w-3 h-3 text-emerald-600 dark:text-emerald-400 shrink-0" />
          <span>SHA-256 Validated</span>
          <span>·</span>
          <span>ISO/IEC 27001</span>
          <span>·</span>
          <span>© 2025</span>
        </div>
      </div>
    </footer>
  );
};
