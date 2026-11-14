import React, { useState } from 'react';
import { 
  ShieldCheck, 
  Menu, 
  X, 
  Sun, 
  Moon 
} from 'lucide-react';
import { NavTabId, NavTabItem } from '../../types';
import logoImg from '../../assets/Logo.png';

interface NavbarProps {
  activeTab: NavTabId;
  onTabChange: (tab: NavTabId) => void;
  darkMode: boolean;
  onToggleDarkMode: () => void;
  onOpenClearanceModal?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  onTabChange,
  darkMode,
  onToggleDarkMode,
  onOpenClearanceModal,
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems: NavTabItem[] = [
    { id: 'pasarela', label: 'Pasarela' },
    { id: 'chat', label: 'Chat IA', hasDot: true, dotColor: 'bg-indigo-500' },
    { id: 'ledger', label: 'Ledger' },
    { id: 'explicabilidad', label: 'Explicabilidad' },
    { id: 'canal', label: 'Canal Seguro', hasDot: true, dotColor: 'bg-emerald-500' },
  ];

  return (
    <header className="sticky top-0 z-40 bg-white/90 dark:bg-[#0b0f19]/90 backdrop-blur-md border-b border-slate-200/80 dark:border-slate-800 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 min-h-[84px] md:min-h-[92px] py-2 sm:py-2.5 flex items-center justify-between gap-4">
        
        {/* Brand Logo and Live Status Indicator */}
        <div className="flex items-center space-x-3 shrink-0">
          <button 
            onClick={() => onTabChange('pasarela')}
            className="flex items-center focus:outline-hidden text-left group"
          >
            <img 
              src={logoImg} 
              alt="Aduana IA" 
              className="h-14 sm:h-16 md:h-[76px] lg:h-[84px] w-auto object-contain rounded-xl shadow-xs hover:opacity-95 transition-all"
            />
          </button>

          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/60">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            Online
          </span>
        </div>

        {/* Center Segmented Navigation Bar */}
        <nav 
          aria-label="Main Navigation" 
          className="hidden md:flex items-center bg-slate-100 dark:bg-slate-800/80 p-1.5 rounded-full border border-slate-200 dark:border-slate-700/60 shadow-inner text-sm font-medium text-slate-600 dark:text-slate-300"
        >
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                className={`px-5 py-1.5 rounded-full transition-all flex items-center gap-1.5 text-xs font-semibold tracking-wide ${
                  isActive
                    ? 'bg-white dark:bg-slate-700 shadow-sm text-slate-900 dark:text-white font-bold'
                    : 'hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <span>{item.label}</span>
                {item.hasDot && (
                  <span className={`w-2 h-2 rounded-full ${item.dotColor || 'bg-emerald-500'}`} />
                )}
              </button>
            );
          })}
        </nav>

        {/* Right Actions: Theme Toggle and Profile Avatar */}
        <div className="flex items-center space-x-3">
          
          {/* Day / Night Toggle Pill */}
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

          {/* User Profile Badge (CM Auditor) */}
          <button
            onClick={() => {
              if (onOpenClearanceModal) {
                onOpenClearanceModal();
              } else {
                onTabChange('canal');
              }
            }}
            className="flex items-center space-x-2 pl-2 pr-3 py-1 bg-white dark:bg-slate-800 rounded-full border border-slate-200 dark:border-slate-700 hover:border-[#4f46e5] dark:hover:border-indigo-400 transition-all shadow-xs"
            title="Carlos Méndez — Auditor Principal"
          >
            <span className="w-7 h-7 rounded-full bg-[#4f46e5]/10 dark:bg-indigo-950/60 text-[#4f46e5] dark:text-indigo-300 font-bold text-xs flex items-center justify-center">
              CM
            </span>
            <span className="text-xs font-semibold text-slate-700 dark:text-slate-200 hidden sm:inline">
              Auditor
            </span>
          </button>

          {/* Mobile menu button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-lg text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 focus:outline-hidden"
            aria-label="Abrir navegación móvil"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>

        </div>

      </div>

      {/* Mobile drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0b0f19] px-4 pt-3 pb-4 space-y-1.5 animate-in fade-in duration-150">
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  onTabChange(item.id);
                  setMobileMenuOpen(false);
                }}
                className={`w-full text-left px-3.5 py-2.5 rounded-xl text-xs font-semibold flex items-center justify-between transition-colors ${
                  isActive
                    ? 'bg-indigo-50 dark:bg-indigo-950/60 text-[#4f46e5] dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800'
                    : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
                }`}
              >
                <div className="flex items-center gap-2">
                  <span>{item.label}</span>
                  {item.hasDot && (
                    <span className={`w-2 h-2 rounded-full ${item.dotColor || 'bg-emerald-500'}`} />
                  )}
                </div>
                {isActive && <span className="w-1.5 h-1.5 rounded-full bg-[#4f46e5]" />}
              </button>
            );
          })}
        </div>
      )}
    </header>
  );
};
