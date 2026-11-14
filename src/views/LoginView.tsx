import React, { useState } from 'react';
import { 
  ShieldCheck, 
  Lock, 
  UserCheck, 
  KeyRound, 
  Building2, 
  ArrowRight, 
  Sun, 
  Moon, 
  CheckCircle2, 
  AlertCircle,
  Fingerprint
} from 'lucide-react';
import { AuthUser, UserRole } from '../types/auth';
import { LOGIN_PRESETS, MOCK_AUTH_USERS } from '../constants/mockAuth';
import logoImg from '../assets/Logo.png';
import logoWhiteImg from '../assets/Logo-white.png';

interface LoginViewProps {
  onLogin: (user: AuthUser) => void;
  darkMode: boolean;
  onToggleDarkMode: () => void;
}

export const LoginView: React.FC<LoginViewProps> = ({
  onLogin,
  darkMode,
  onToggleDarkMode,
}) => {
  const [selectedRole, setSelectedRole] = useState<UserRole>('auditor');
  const [emailInput, setEmailInput] = useState<string>(MOCK_AUTH_USERS.auditor.email);
  const [passwordInput, setPasswordInput] = useState<string>('auditor2026');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isAuthenticating, setIsAuthenticating] = useState(false);

  // When clicking a preset card, auto-fill the login form
  const handleSelectPreset = (presetRole: UserRole) => {
    setSelectedRole(presetRole);
    const preset = LOGIN_PRESETS.find(p => p.role === presetRole);
    if (preset) {
      setEmailInput(preset.user.email);
      setPasswordInput(preset.defaultPass);
      setErrorMsg(null);
    }
  };

  const handleQuickLogin = (role: UserRole) => {
    const targetUser = MOCK_AUTH_USERS[role];
    if (targetUser) {
      setIsAuthenticating(true);
      setTimeout(() => {
        setIsAuthenticating(false);
        onLogin(targetUser);
      }, 350);
    }
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setIsAuthenticating(true);

    setTimeout(() => {
      // Find matching user by email
      const matchedUser = Object.values(MOCK_AUTH_USERS).find(
        u => u.email.toLowerCase() === emailInput.trim().toLowerCase()
      );

      if (!matchedUser) {
        setErrorMsg('Usuario o correo institucional no registrado en el nodo local.');
        setIsAuthenticating(false);
        return;
      }

      // Check password preset
      const preset = LOGIN_PRESETS.find(p => p.role === matchedUser.role);
      if (preset && passwordInput !== preset.defaultPass) {
        setErrorMsg('Contraseña o credencial Ed25519 inválida para este rol.');
        setIsAuthenticating(false);
        return;
      }

      setIsAuthenticating(false);
      onLogin(matchedUser);
    }, 400);
  };

  return (
    <div className="min-h-screen flex flex-col justify-between bg-[#F4F6FB] dark:bg-[#060a12] text-slate-800 dark:text-slate-100 transition-colors select-none">
      {/* Top Bar with Brand and Theme Toggle */}
      <header className="px-6 py-4 flex items-center justify-between border-b border-neutral-200/80 dark:border-neutral-800/80 bg-white/70 dark:bg-[#0c121e]/70 backdrop-blur-md">
        <div className="flex items-center gap-3">
          {/* Logo */}
          <div className="flex items-center">
            <img 
              src={logoImg} 
              alt="Aduana IA" 
              className="block dark:hidden h-12 sm:h-14 w-auto object-contain"
            />
            <img 
              src={logoWhiteImg} 
              alt="Aduana IA" 
              className="hidden dark:block h-12 sm:h-14 w-auto object-contain drop-shadow-[0_0_12px_rgba(255,255,255,0.25)]"
            />
          </div>
          <div className="hidden sm:block border-l border-neutral-300 dark:border-neutral-700 pl-3">
            <span className="text-xs font-semibold text-neutral-900 dark:text-white block">
              Gobernanza Algorítmica Soberana
            </span>
            <span className="text-[10px] text-neutral-500 dark:text-neutral-400 block font-mono">
              Consorcio GovTech • Nodo Soberano #01
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onToggleDarkMode}
            aria-label="Cambiar tema día/noche"
            className="p-2 rounded-xl text-neutral-500 hover:text-neutral-800 dark:text-neutral-400 dark:hover:text-neutral-200 hover:bg-neutral-200/60 dark:hover:bg-neutral-800/70 transition-colors"
          >
            {darkMode ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-indigo-600" />}
          </button>
        </div>
      </header>

      {/* Main Login Content */}
      <main className="flex-1 flex items-center justify-center p-4 sm:p-6 lg:p-8">
        <div className="w-full max-w-4xl space-y-8">
          {/* Title and Intro */}
          <div className="text-center space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 text-xs font-semibold border border-indigo-200/50 dark:border-indigo-800/50 mb-1">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Autenticación de Enclave Criptográfico Zero-Trust</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-neutral-900 dark:text-white">
              Inicio de Sesión por Roles
            </h1>
            <p className="text-xs sm:text-sm text-neutral-500 dark:text-neutral-400 max-w-xl mx-auto">
              Seleccione uno de los 3 perfiles oficiales para acceder de inmediato al entorno de auditoría, trámite aduanero o control perimetral.
            </p>
          </div>

          {/* 3 User Roles Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {LOGIN_PRESETS.map((preset) => {
              const isSelected = selectedRole === preset.role;
              return (
                <div
                  key={preset.role}
                  onClick={() => handleSelectPreset(preset.role)}
                  className={`cursor-pointer rounded-2xl p-5 border transition-all duration-200 flex flex-col justify-between text-left relative ${
                    isSelected
                      ? 'bg-white dark:bg-[#111827] border-primary shadow-lg ring-2 ring-primary/20 scale-[1.02]'
                      : 'bg-white/80 dark:bg-[#0c121e] border-neutral-200 dark:border-neutral-800 hover:border-neutral-300 dark:hover:border-neutral-700 shadow-sm'
                  }`}
                >
                  <div className="space-y-3">
                    {/* Header with Avatar & Role Tag */}
                    <div className="flex items-center justify-between">
                      <div className="w-10 h-10 rounded-xl bg-[#141b29] text-indigo-300 font-bold text-sm flex items-center justify-center border border-indigo-500/30">
                        {preset.user.avatarText}
                      </div>
                      <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${preset.badgeColor}`}>
                        {preset.user.credentials.clearanceLevel.split('—')[0].trim()}
                      </span>
                    </div>

                    <div>
                      <h3 className="text-sm font-bold text-neutral-900 dark:text-white">
                        {preset.roleName}
                      </h3>
                      <p className="text-xs font-semibold text-primary dark:text-indigo-400">
                        {preset.user.name}
                      </p>
                    </div>

                    <p className="text-[11px] text-neutral-600 dark:text-neutral-400 leading-relaxed">
                      {preset.description}
                    </p>

                    <div className="pt-2 text-[10px] font-mono text-neutral-400 dark:text-neutral-500 border-t border-neutral-100 dark:border-neutral-800 space-y-1">
                      <div>Usuario: <span className="text-neutral-700 dark:text-neutral-300">{preset.user.email}</span></div>
                      <div>Clave: <span className="text-neutral-700 dark:text-neutral-300">{preset.defaultPass}</span></div>
                    </div>
                  </div>

                  {/* Direct One-Click Enter Button */}
                  <div className="pt-4">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleQuickLogin(preset.role);
                      }}
                      disabled={isAuthenticating}
                      className="w-full py-2 px-3 rounded-xl text-xs font-semibold bg-primary hover:bg-indigo-700 text-white shadow-xs transition-all active:scale-95 flex items-center justify-center gap-1.5"
                    >
                      <span>Acceder como {preset.roleName}</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Manual Credentials Box */}
          <div className="max-w-md mx-auto p-6 rounded-2xl bg-white dark:bg-[#0c121e] border border-neutral-200 dark:border-neutral-800 shadow-md space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-neutral-100 dark:border-neutral-800">
              <span className="text-xs font-bold text-neutral-900 dark:text-white uppercase tracking-wider">
                Verificación Manual de Credenciales
              </span>
              <span className="text-[10px] font-mono text-neutral-400">Ed25519 Enclave</span>
            </div>

            {errorMsg && (
              <div className="p-3 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800/60 text-xs text-red-700 dark:text-red-300 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-red-500 shrink-0" />
                <span>{errorMsg}</span>
              </div>
            )}

            <form onSubmit={handleFormSubmit} className="space-y-3.5">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-neutral-700 dark:text-neutral-300 flex items-center gap-1.5">
                  <UserCheck className="w-3.5 h-3.5 text-neutral-400" />
                  <span>Usuario o Correo Institucional:</span>
                </label>
                <input
                  type="text"
                  value={emailInput}
                  onChange={(e) => setEmailInput(e.target.value)}
                  placeholder="ej. auditor@aduana.gob.ve"
                  required
                  className="w-full px-3 py-2 rounded-xl text-xs bg-neutral-50 dark:bg-[#141b29] border border-neutral-200 dark:border-neutral-700 text-neutral-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary/30"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-neutral-700 dark:text-neutral-300 flex items-center gap-1.5">
                  <Lock className="w-3.5 h-3.5 text-neutral-400" />
                  <span>Contraseña o Passkey Criptográfica:</span>
                </label>
                <input
                  type="password"
                  value={passwordInput}
                  onChange={(e) => setPasswordInput(e.target.value)}
                  placeholder="••••••••••••"
                  required
                  className="w-full px-3 py-2 rounded-xl text-xs bg-neutral-50 dark:bg-[#141b29] border border-neutral-200 dark:border-neutral-700 text-neutral-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary/30"
                />
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={isAuthenticating}
                  className="w-full py-2.5 px-4 rounded-xl text-xs font-semibold bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 hover:bg-neutral-800 dark:hover:bg-neutral-100 shadow-sm transition-all active:scale-95 flex items-center justify-center gap-2"
                >
                  <Fingerprint className="w-4 h-4" />
                  <span>{isAuthenticating ? 'Validando en Enclave...' : 'Iniciar Sesión Segura'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="px-6 py-4 border-t border-neutral-200/80 dark:border-neutral-800/80 text-center text-[11px] font-mono text-neutral-400 dark:text-neutral-500 bg-white/70 dark:bg-[#0c121e]/70">
        República Bolivariana de Venezuela • Consorcio GovTech • ISO/IEC 27001 Validated • Cero fugas de información clasificable
      </footer>
    </div>
  );
};
