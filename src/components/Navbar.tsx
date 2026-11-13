import React, { useState } from 'react';
import { 
  ShieldCheck, 
  Moon, 
  Sun, 
  Menu, 
  X, 
  User
} from 'lucide-react';

export type NavTab = 'pasarela' | 'ledger' | 'explicabilidad';

interface NavbarProps {
  activeTab: NavTab;
  onTabChange: (tab: NavTab) => void;
  darkMode: boolean;
  onToggleDarkMode: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  onTabChange,
  darkMode,
  onToggleDarkMode,
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems: { id: NavTab; label: string }[] = [
    { id: 'pasarela', label: 'Pasarela' },
    { id: 'ledger', label: 'Ledger' },
    { id: 'explicabilidad', label: 'Explicabilidad' },
  ];

  return (
    <header className="sticky top-0 z-40 w-full bg-white/95 dark:bg-[#0f1422]/95 backdrop-blur-md border-b border-slate-200/80 dark:border-slate-800 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Left Brand + Status */}
          <div className="flex items-center gap-3 sm:gap-4">
            <button 
              onClick={() => onTabChange('ledger')}
              className="flex items-center gap-2 group text-left focus:outline-hidden"
            >
              <div className="w-8 h-8 rounded-lg bg-[#3525cd] flex items-center justify-center text-white shadow-xs group-hover:bg-indigo-600 transition-colors">
                <ShieldCheck className="w-5 h-5" strokeWidth={2} />
              </div>
              <span className="font-bold text-lg tracking-tight text-slate-900 dark:text-white">
                Aduana <span className="text-[#3525cd] dark:text-indigo-400">IA</span>
              </span>
            </button>

            {/* Status Pill */}
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200/80 dark:bg-emerald-950/50 dark:text-emerald-400 dark:border-emerald-800/80 select-none">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>EN LÍNEA</span>
            </div>
          </div>

          {/* Center Navigation Tabs (Desktop / Tablet) */}
          <nav className="hidden md:flex items-center space-x-1 p-1 bg-slate-100/90 dark:bg-slate-800/80 rounded-full border border-slate-200/60 dark:border-slate-700/60">
            {navItems.map((item) => {
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onTabChange(item.id)}
                  className={`px-5 py-1.5 rounded-full text-xs font-semibold tracking-wide transition-all duration-150 ${
                    isActive
                      ? 'bg-white dark:bg-slate-900 text-[#3525cd] dark:text-indigo-400 shadow-xs'
                      : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white'
                  }`}
                >
                  {item.label}
                </button>
              );
            })}
          </nav>

          {/* Right Controls */}
          <div className="flex items-center gap-2 sm:gap-3">
            {/* Dark Mode Toggle */}
            <button
              onClick={onToggleDarkMode}
              className="p-2 rounded-lg text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors focus:outline-hidden"
              title={darkMode ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'}
              aria-label="Toggle theme"
            >
              {darkMode ? (
                <Sun className="w-4 h-4 text-amber-400" strokeWidth={2} />
              ) : (
                <Moon className="w-4 h-4" strokeWidth={2} />
              )}
            </button>

            {/* User Profile Avatar */}
            <div className="relative group">
              <button 
                className="w-8 h-8 rounded-full bg-[#3525cd] text-white flex items-center justify-center hover:ring-2 hover:ring-indigo-300 dark:hover:ring-indigo-800 transition-all focus:outline-hidden"
                title="Funcionario Auditor: L. Santander (DGA-08)"
              >
                <User className="w-4 h-4" strokeWidth={2} />
              </button>
            </div>

            {/* Mobile Menu Toggle Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 rounded-lg text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 focus:outline-hidden"
              aria-label="Menu"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>

        </div>
      </div>

      {/* Mobile Drawer Navigation */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0f1422] px-4 pt-3 pb-4 space-y-2 animate-in fade-in slide-in-from-top-2 duration-150">
          <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 px-3 py-1 font-semibold">
            Módulos Soberanos
          </div>
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  onTabChange(item.id);
                  setMobileMenuOpen(false);
                }}
                className={`w-full text-left px-3.5 py-2.5 rounded-lg text-sm font-semibold flex items-center justify-between transition-colors ${
                  isActive
                    ? 'bg-indigo-50 dark:bg-indigo-950/60 text-[#3525cd] dark:text-indigo-400 border border-indigo-200/60 dark:border-indigo-800/60'
                    : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
                }`}
              >
                <span>{item.label}</span>
                {isActive && <span className="w-1.5 h-1.5 rounded-full bg-[#3525cd] dark:bg-indigo-400" />}
              </button>
            );
          })}
          
          <div className="pt-2 border-t border-slate-100 dark:border-slate-800 text-xs text-slate-500 font-mono px-3">
            Nodo: #01-Soberano · Quórum 8/8
          </div>
        </div>
      )}
    </header>
  );
};
