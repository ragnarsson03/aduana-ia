import React, { useState, useRef } from 'react';
import { 
  ShieldCheck, 
  Lock, 
  UserCheck, 
  KeyRound, 
  ArrowRight, 
  Sun, 
  Moon, 
  CheckCircle2, 
  AlertCircle,
  Fingerprint,
  X,
  Eye,
  EyeOff
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
  // Selected role is null initially so the manual verification box is hidden by default
  const [selectedRole, setSelectedRole] = useState<UserRole | null>(null);
  const [emailInput, setEmailInput] = useState<string>('');
  const [passwordInput, setPasswordInput] = useState<string>('');
  const [showPassword, setShowPassword] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const formRef = useRef<HTMLDivElement>(null);

  // When clicking on a role's "Acceder como [Rol]" button, activate that role and reveal the credential prompt
  const handleSelectRole = (role: UserRole) => {
    setSelectedRole(role);
    const targetUser = MOCK_AUTH_USERS[role];
    const preset = LOGIN_PRESETS.find(p => p.role === role);
    if (targetUser && preset) {
      setEmailInput(targetUser.email);
      setPasswordInput(preset.defaultPass);
      setErrorMsg(null);
    }
    // Smooth scroll down to the credential verification box
    setTimeout(() => {
      formRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 120);
  };

  const handleCancelSelection = () => {
    setSelectedRole(null);
    setEmailInput('');
    setPasswordInput('');
    setErrorMsg(null);
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

  const activePreset = selectedRole ? LOGIN_PRESETS.find(p => p.role === selectedRole) : null;
  const activeUser = selectedRole ? MOCK_AUTH_USERS[selectedRole] : null;

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
                  onClick={() => handleSelectRole(preset.role)}
                  className={`cursor-pointer rounded-2xl p-5 border transition-all duration-200 flex flex-col justify-between text-left relative ${
                    isSelected
                      ? 'bg-white dark:bg-[#111827] border-primary shadow-xl ring-2 ring-primary/40 scale-[1.02]'
                      : 'bg-white/80 dark:bg-[#0c121e] border-neutral-200 dark:border-neutral-800 hover:border-neutral-300 dark:hover:border-neutral-700 shadow-sm hover:shadow-md'
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
                      <div>Usuario: <span className="text-neutral-700 dark:text-neutral-300 font-medium">{preset.user.email}</span></div>
                      <div>Clave: <span className="text-neutral-700 dark:text-neutral-300 font-medium">{preset.defaultPass}</span></div>
                    </div>
                  </div>

                  {/* Acceder como [Rol] Button */}
                  <div className="pt-4">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSelectRole(preset.role);
                      }}
                      className={`w-full py-2 px-3 rounded-xl text-xs font-semibold transition-all active:scale-95 flex items-center justify-center gap-1.5 shadow-xs ${
                        isSelected 
                          ? 'bg-primary text-white shadow-md' 
                          : 'bg-primary/90 hover:bg-primary text-white'
                      }`}
                    >
                      <span>{isSelected ? `Ingresando como ${preset.roleName}` : `Acceder como ${preset.roleName}`}</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Conditional Credential Verification Form — Only appears when a role is selected */}
          {selectedRole && activePreset && activeUser && (
            <div 
              ref={formRef}
              className="max-w-md mx-auto p-6 rounded-2xl bg-white dark:bg-[#0c121e] border-2 border-primary/30 dark:border-primary/40 shadow-2xl space-y-4 animate-in fade-in slide-in-from-top-4 duration-300"
            >
              {/* Form Header */}
              <div className="flex items-center justify-between pb-3 border-b border-neutral-100 dark:border-neutral-800">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-primary/10 text-primary dark:text-indigo-400 font-bold text-xs flex items-center justify-center border border-primary/20">
                    {activeUser.avatarText}
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-neutral-900 dark:text-white uppercase tracking-wider">
                      Verificación de Credenciales
                    </h3>
                    <p className="text-[11px] text-neutral-500 dark:text-neutral-400">
                      Rol: <span className="font-semibold text-primary dark:text-indigo-400">{activePreset.roleName}</span> ({activeUser.name})
                    </p>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={handleCancelSelection}
                  className="p-1.5 rounded-lg text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-200 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
                  title="Cancelar y cambiar de rol"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Clearance badge */}
              <div className="p-2.5 rounded-xl bg-indigo-50/60 dark:bg-indigo-950/30 border border-indigo-200/50 dark:border-indigo-800/40 text-[11px] font-mono text-indigo-700 dark:text-indigo-300 flex items-center justify-between">
                <span>{activeUser.credentials.clearanceLevel}</span>
                <span className="text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" />
                  Nodo Local
                </span>
              </div>

              {/* Error Alert */}
              {errorMsg && (
                <div className="p-3 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800/60 text-xs text-red-700 dark:text-red-300 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-red-500 shrink-0" />
                  <span>{errorMsg}</span>
                </div>
              )}

              {/* Form Inputs */}
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
                  <label className="text-xs font-semibold text-neutral-700 dark:text-neutral-300 flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                      <Lock className="w-3.5 h-3.5 text-neutral-400" />
                      <span>Contraseña o Passkey Criptográfica:</span>
                    </span>
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="text-[10px] text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300 flex items-center gap-1"
                    >
                      {showPassword ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                      <span>{showPassword ? 'Ocultar' : 'Mostrar'}</span>
                    </button>
                  </label>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={passwordInput}
                    onChange={(e) => setPasswordInput(e.target.value)}
                    placeholder="••••••••••••"
                    required
                    className="w-full px-3 py-2 rounded-xl text-xs bg-neutral-50 dark:bg-[#141b29] border border-neutral-200 dark:border-neutral-700 text-neutral-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary/30 font-mono"
                  />
                  <p className="text-[10px] text-neutral-400 font-mono">
                    Clave de prueba: <span className="text-neutral-600 dark:text-neutral-300 font-semibold">{activePreset.defaultPass}</span>
                  </p>
                </div>

                <div className="pt-2 flex items-center gap-2">
                  <button
                    type="button"
                    onClick={handleCancelSelection}
                    className="py-2.5 px-3 rounded-xl text-xs font-medium text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
                  >
                    Elegir otro rol
                  </button>

                  <button
                    type="submit"
                    disabled={isAuthenticating}
                    className="flex-1 py-2.5 px-4 rounded-xl text-xs font-semibold bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 hover:bg-neutral-800 dark:hover:bg-neutral-100 shadow-sm transition-all active:scale-95 flex items-center justify-center gap-2"
                  >
                    <Fingerprint className="w-4 h-4" />
                    <span>{isAuthenticating ? 'Validando en Enclave...' : `Confirmar y Entrar como ${activePreset.roleName}`}</span>
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="px-6 py-4 border-t border-neutral-200/80 dark:border-neutral-800/80 text-center text-[11px] font-mono text-neutral-400 dark:text-neutral-500 bg-white/70 dark:bg-[#0c121e]/70">
        República Bolivariana de Venezuela • Consorcio GovTech • ISO/IEC 27001 Validated • Cero fugas de información clasificable
      </footer>
    </div>
  );
};
