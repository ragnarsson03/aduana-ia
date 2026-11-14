import React from 'react';
import { Sun, Moon } from 'lucide-react';
import logoImg from '../../../assets/Logo.png';

interface CanalHeaderProps {
  darkMode: boolean;
  onToggleDarkMode: () => void;
  onNavigateHome?: () => void;
}

export const CanalHeader: React.FC<CanalHeaderProps> = ({
  darkMode,
  onToggleDarkMode,
  onNavigateHome,
}) => {
  return (
    <div className="flex items-center justify-between pb-2 mb-4">
      {/* Title on the left */}
      <button 
        onClick={onNavigateHome}
        className="flex items-center gap-2.5 text-left focus:outline-hidden group"
      >
        <img 
          src={logoImg} 
          alt="Aduana IA" 
          className="h-12 sm:h-14 md:h-16 w-auto object-contain rounded-xl shadow-xs hover:opacity-95 transition-all"
        />
        <span className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
          <span className="text-slate-400 dark:text-slate-500 font-normal">—</span> Canal Seguro
        </span>
        <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse mt-0.5" />
      </button>

      {/* Day / Night switch pill on the right */}
      <button
        onClick={onToggleDarkMode}
        aria-label="Cambiar tema día/noche"
        className="relative inline-flex items-center bg-slate-900 text-slate-100 dark:bg-slate-700 rounded-full p-1 w-16 h-8 cursor-pointer shadow-inner transition-colors duration-200 focus:outline-hidden focus:ring-2 focus:ring-[#4f46e5]"
      >
        <span className="sr-only">Alternar modo oscuro</span>
        {/* Sun icon */}
        <span className="absolute left-2 text-xs text-amber-400 pointer-events-none">
          <Sun className="w-3.5 h-3.5" />
        </span>
        {/* Moon icon */}
        <span className="absolute right-2 text-xs text-indigo-300 pointer-events-none">
          <Moon className="w-3.5 h-3.5" />
        </span>
        {/* Active circle selector */}
        <span 
          className={`inline-block w-6 h-6 transform transition-transform duration-200 ease-in-out bg-white dark:bg-slate-200 rounded-full shadow-sm ${
            darkMode ? 'translate-x-8' : 'translate-x-0'
          }`}
        />
      </button>
    </div>
  );
};
