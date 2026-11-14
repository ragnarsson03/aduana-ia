import React, { useState, useRef, useEffect } from 'react';
import { 
  ShieldCheck, 
  Menu, 
  X, 
  Sun, 
  Moon,
  ChevronDown,
  User,
  Settings,
  LogOut
} from 'lucide-react';
import { NavTabId, NavTabItem } from '../../types';
import { AuthUser } from '../../types/auth';
import logoImg from '../../assets/Logo.png';
import logoWhiteImg from '../../assets/Logo-white.png';

interface NavbarProps {
  activeTab: NavTabId;
  onTabChange: (tab: NavTabId) => void;
  darkMode: boolean;
  onToggleDarkMode: () => void;
  currentUser?: AuthUser | null;
  onLogout?: () => void;
  onNavigateProfile?: (section?: 'profile' | 'settings') => void;
  onOpenClearanceModal?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  onTabChange,
  darkMode,
  onToggleDarkMode,
  currentUser,
  onLogout,
  onNavigateProfile,
  onOpenClearanceModal,
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setProfileDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const allNavItems: NavTabItem[] = [
    { id: 'pasarela', label: 'Pasarela' },
    { id: 'chat', label: 'Nexus IA', hasDot: true, dotColor: 'bg-indigo-500' },
    { id: 'ledger', label: 'Ledger' },
    { id: 'explicabilidad', label: 'Explicabilidad' },
    { id: 'canal', label: 'Canal Seguro', hasDot: true, dotColor: 'bg-emerald-500' },
  ];

  // Filter based on user's authorized role tabs
  const allowedTabs = currentUser ? currentUser.allowedTabs : allNavItems.map(i => i.id);
  const navItems = allNavItems.filter(item => allowedTabs.includes(item.id));
  const homeTab = currentUser ? currentUser.defaultTab : 'pasarela';

  return (
    <header className="sticky top-0 z-40 bg-white/90 dark:bg-[#0b0f19]/90 backdrop-blur-md border-b border-slate-200/80 dark:border-slate-800 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 min-h-[84px] md:min-h-[92px] py-2 sm:py-2.5 flex items-center justify-between gap-4">
        
        {/* Brand Logo and Live Status Indicator */}
        <div className="flex items-center space-x-3 shrink-0">
          <button 
            onClick={() => onTabChange(homeTab)}
            className="flex items-center focus:outline-hidden text-left group"
          >
            {/* Logo en Modo Claro */}
            <img 
              src={logoImg} 
              alt="Aduana IA" 
              className="block dark:hidden h-14 sm:h-16 md:h-[76px] lg:h-[84px] w-auto object-contain rounded-xl shadow-xs hover:opacity-95 transition-all"
            />
            {/* Logo en Modo Oscuro (Adaptado para fondo oscuro con detalles y colores originales) */}
            <img 
              src={logoWhiteImg} 
              alt="Aduana IA" 
              className="hidden dark:block h-14 sm:h-16 md:h-[76px] lg:h-[84px] w-auto object-contain rounded-xl shadow-xs hover:opacity-95 transition-all drop-shadow-[0_4px_12px_rgba(0,0,0,0.5)] hover:drop-shadow-[0_0_14px_rgba(79,70,229,0.3)]"
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
                className={`relative px-4 py-1.5 rounded-full transition-all duration-200 flex items-center space-x-1.5 text-xs font-semibold ${
                  isActive
                    ? 'bg-white dark:bg-[#4f46e5] text-slate-900 dark:text-white shadow-sm'
                    : 'hover:text-slate-900 dark:hover:text-white hover:bg-slate-200/50 dark:hover:bg-slate-700/50'
                }`}
              >
                <span>{item.label}</span>
                {item.hasDot && (
                  <span className={`w-1.5 h-1.5 rounded-full ${item.dotColor || 'bg-indigo-500'} animate-pulse`} />
                )}
                {item.badge && (
                  <span className="text-[10px] px-1.5 py-0.2 bg-indigo-100 dark:bg-indigo-900/60 text-indigo-700 dark:text-indigo-300 rounded-full">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Right Actions: Theme Toggle and Profile Avatar Pill */}
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

          {/* User Profile Badge & Dropdown Menu (Matches Image 1) */}
          {currentUser ? (
            <div className="relative" ref={dropdownRef}>
              <button
                type="button"
                onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
                className="flex items-center gap-2 p-1 pr-2.5 rounded-full bg-neutral-100 hover:bg-neutral-200/80 dark:bg-neutral-800/80 dark:hover:bg-neutral-700/80 border border-neutral-200/80 dark:border-neutral-700/70 transition-all select-none focus:outline-none active:scale-95 shadow-xs"
                title={`${currentUser.name} — ${currentUser.roleLabel}`}
                aria-expanded={profileDropdownOpen}
              >
                <div className="relative shrink-0">
                  <div className="w-7 h-7 rounded-full bg-primary/10 dark:bg-primary/20 text-primary dark:text-indigo-400 font-bold text-xs flex items-center justify-center border border-primary/20">
                    {currentUser.avatarText}
                  </div>
                  <span className="w-2 h-2 rounded-full bg-emerald-500 absolute -bottom-0.5 -right-0.5 ring-2 ring-white dark:ring-[#090d16]" />
                </div>
                <span className="text-xs font-semibold text-neutral-800 dark:text-neutral-200 hidden sm:inline">
                  {currentUser.shortName}
                </span>
                <ChevronDown className={`w-3.5 h-3.5 text-neutral-400 dark:text-neutral-500 transition-transform duration-200 ${profileDropdownOpen ? 'rotate-180' : ''}`} />
              </button>

              {/* Popover Dropdown Card (Image 1) */}
              {profileDropdownOpen && (
                <div className="absolute top-full right-0 mt-2 w-64 rounded-xl bg-white dark:bg-[#111827] border border-neutral-200 dark:border-neutral-800 shadow-xl z-50 p-2 text-left origin-top-right transition-all animate-fade-in">
                  {/* Popover Header */}
                  <div className="px-3 py-2.5">
                    <div className="flex items-center gap-2.5">
                      <div className="w-9 h-9 rounded-full bg-primary/10 dark:bg-primary/20 text-primary font-bold text-xs flex items-center justify-center shrink-0 border border-primary/20 shadow-xs">
                        {currentUser.avatarText}
                      </div>
                      <div className="min-w-0 flex-1">
                        <h4 className="text-sm font-semibold text-neutral-900 dark:text-white truncate leading-tight">
                          {currentUser.name}
                        </h4>
                        <span className="inline-block mt-1 px-2 py-0.5 text-[10px] font-medium text-primary dark:text-indigo-400 bg-primary/10 dark:bg-primary/20 rounded-full">
                          {currentUser.roleLabel}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Divider */}
                  <div className="border-b border-neutral-100 dark:border-neutral-800/80 my-1" />

                  {/* Menu Items */}
                  <div className="space-y-0.5 py-1 text-xs">
                    <button
                      type="button"
                      onClick={() => {
                        setProfileDropdownOpen(false);
                        if (onNavigateProfile) {
                          onNavigateProfile('profile');
                        } else {
                          onTabChange('perfil');
                        }
                      }}
                      className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800/70 transition-all text-left group"
                    >
                      <User className="w-4 h-4 text-neutral-400 group-hover:text-primary dark:group-hover:text-indigo-400 transition-colors" />
                      <span className="group-hover:text-neutral-900 dark:group-hover:text-white font-medium transition-colors">
                        Ver perfil
                      </span>
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        setProfileDropdownOpen(false);
                        if (onNavigateProfile) {
                          onNavigateProfile('settings');
                        } else {
                          onTabChange('perfil');
                        }
                      }}
                      className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800/70 transition-all text-left group"
                    >
                      <Settings className="w-4 h-4 text-neutral-400 group-hover:text-primary dark:group-hover:text-indigo-400 transition-colors" />
                      <span className="group-hover:text-neutral-900 dark:group-hover:text-white font-medium transition-colors">
                        Ajustes
                      </span>
                    </button>
                  </div>

                  {/* Divider */}
                  <div className="border-b border-neutral-100 dark:border-neutral-800/80 my-1" />

                  {/* Logout Option */}
                  <div className="pt-0.5">
                    <button
                      type="button"
                      onClick={() => {
                        setProfileDropdownOpen(false);
                        onLogout?.();
                      }}
                      className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30 transition-all text-left text-xs font-semibold group"
                    >
                      <LogOut className="w-4 h-4 text-red-500 transition-transform group-hover:scale-110" />
                      <span>Cerrar sesión</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <button
              onClick={() => onTabChange('perfil')}
              className="flex items-center space-x-2 pl-2 pr-3 py-1 bg-white dark:bg-slate-800 rounded-full border border-slate-200 dark:border-slate-700 hover:border-[#4f46e5] text-xs font-semibold text-slate-700 dark:text-slate-200"
            >
              Iniciar Sesión
            </button>
          )}

          {/* Mobile menu button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-lg text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 focus:outline-hidden"
            aria-label="Abrir navegación móvil"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Dropdown Menu Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0b0f19] px-4 pt-2 pb-4 space-y-1">
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  onTabChange(item.id);
                  setMobileMenuOpen(false);
                }}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm font-semibold flex items-center justify-between ${
                  isActive
                    ? 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white'
                    : 'text-slate-600 dark:text-slate-400'
                }`}
              >
                <span>{item.label}</span>
                {item.hasDot && (
                  <span className={`w-2 h-2 rounded-full ${item.dotColor || 'bg-indigo-500'}`} />
                )}
              </button>
            );
          })}
        </div>
      )}
    </header>
  );
};
