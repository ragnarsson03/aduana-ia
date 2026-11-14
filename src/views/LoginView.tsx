import React, { useState } from 'react';
import { 
  ShieldCheck, 
  Shield, 
  Lock, 
  Unlock, 
  User, 
  ArrowRight, 
  CheckCircle2, 
  ExternalLink, 
  Sun, 
  Moon, 
  AlertCircle,
  KeyRound,
  X,
  FileCheck
} from 'lucide-react';
import { AuthUser, UserRole } from '../types/auth';
import { MOCK_AUTH_USERS } from '../constants/mockAuth';
import loginBgImg from '../assets/login-bg.jpg';

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
  const [emailInput, setEmailInput] = useState<string>('auditor.soberano@enclave.aduana.gob');
  const [passwordInput, setPasswordInput] = useState<string>('auditor2026');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberNode, setRememberNode] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isAuthenticating, setIsAuthenticating] = useState(false);

  // Modals for footer / passkey links
  const [showHardwareTokenModal, setShowHardwareTokenModal] = useState(false);
  const [showForgotModal, setShowForgotModal] = useState(false);

  const roleCredentialsMap: Record<UserRole, { email: string; pass: string; label: string; clearance: string }> = {
    auditor: {
      email: 'auditor.soberano@enclave.aduana.gob',
      pass: 'auditor2026',
      label: 'Auditor',
      clearance: 'Nivel 4 — Confidencial Estatal'
    },
    analista: {
      email: 'analista.operaciones@enclave.aduana.gob',
      pass: 'analista2026',
      label: 'Analista',
      clearance: 'Nivel 2 — Operativo Aduanero'
    },
    admin: {
      email: 'admin.infraestructura@enclave.aduana.gob',
      pass: 'admin2026',
      label: 'Administrador',
      clearance: 'Nivel 5 — Soberanía Crítica'
    }
  };

  const handleSelectRoleTab = (role: UserRole) => {
    setSelectedRole(role);
    const cred = roleCredentialsMap[role];
    setEmailInput(cred.email);
    setPasswordInput(cred.pass);
    setErrorMsg(null);
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setIsAuthenticating(true);

    setTimeout(() => {
      const emailClean = emailInput.trim().toLowerCase();

      // Find user by role or email match
      let matchedUser: AuthUser | undefined = undefined;

      if (emailClean.includes('auditor') || emailClean === 'auditor@aduana.gob.ve' || emailClean === 'auditor.soberano@enclave.aduana.gob') {
        matchedUser = MOCK_AUTH_USERS.auditor;
      } else if (emailClean.includes('analista') || emailClean === 'analista@aduana.gob.ve' || emailClean === 'analista.operaciones@enclave.aduana.gob') {
        matchedUser = MOCK_AUTH_USERS.analista;
      } else if (emailClean.includes('admin') || emailClean === 'admin@aduana.gob.ve' || emailClean === 'admin.infraestructura@enclave.aduana.gob') {
        matchedUser = MOCK_AUTH_USERS.admin;
      } else {
        // Fallback to active selected role
        matchedUser = MOCK_AUTH_USERS[selectedRole];
      }

      if (!matchedUser) {
        setErrorMsg('Credencial no registrada en el enclave del nodo local.');
        setIsAuthenticating(false);
        return;
      }

      setIsAuthenticating(false);
      onLogin(matchedUser);
    }, 450);
  };

  return (
    <div className="relative min-h-screen flex flex-col justify-center items-center bg-[#0f131d] text-[#dfe2f1] overflow-x-hidden selection:bg-indigo-600 selection:text-white select-none">
      
      {/* Ambient Cinematic Deep Background with Cryptographic NOC Mesh (Matches code.html & image) */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        <img 
          alt="Aduana IA Control Center" 
          src={loginBgImg} 
          className="w-full h-full object-cover object-center opacity-30 filter brightness-[0.45] contrast-125 scale-105"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-[#0f131d] via-[#0f131d]/85 to-transparent" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(79,70,229,0.22)_0%,transparent_70%)]" />
      </div>

      {/* Top Floating Controls */}
      <div className="absolute top-4 right-6 z-30 flex items-center gap-3">
        <button
          onClick={onToggleDarkMode}
          aria-label="Alternar tema"
          className="p-2 rounded-xl text-slate-400 hover:text-white bg-[#171b26]/70 hover:bg-[#262a35] border border-white/10 backdrop-blur-md transition-all"
        >
          {darkMode ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-indigo-400" />}
        </button>
      </div>

      {/* Main Login Canvas / Glass Enclave Container (Matches code.html & image) */}
      <main className="relative z-10 w-full max-w-[480px] px-4 py-8 mx-auto flex flex-col items-center">
        
        {/* Glass Specimen Card */}
        <div className="w-full rounded-2xl p-6 sm:p-8 backdrop-blur-2xl bg-[#0d1527]/80 border border-indigo-500/30 shadow-[0_0_35px_-4px_rgba(79,70,229,0.35)] relative overflow-hidden transition-all duration-300">
          
          {/* Top Hairline Gradient Accent */}
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-[#4f46e5] to-transparent opacity-85" />

          {/* Card Header */}
          <div className="text-center mb-5">
            {/* Elevated Shield Icon */}
            <div className="inline-flex items-center justify-center p-3 rounded-2xl bg-[#171b26] border border-indigo-500/40 mb-3 shadow-[0_0_22px_rgba(79,70,229,0.35)] text-indigo-400">
              <Shield className="w-8 h-8 fill-indigo-400/20 stroke-indigo-400" />
            </div>

            <h1 className="text-2xl sm:text-[28px] font-bold text-white tracking-tight">
              Acceso Criptográfico
            </h1>
            <p className="text-xs text-[#c7c4d8] mt-1 font-sans">
              Infraestructura Crítica de Control Fronterizo y Aduanal
            </p>

            {/* Hardware Secure Enclave Validated Pill */}
            <div className="inline-flex items-center space-x-1.5 mt-3 px-3 py-1 rounded-full bg-[#0a0e18]/85 border border-white/10 text-[11px] font-mono text-[#4edea3]">
              <span className="w-2 h-2 rounded-full bg-[#4edea3] animate-pulse" />
              <span>Hardware Secure Enclave Validated (AES-256 / SHA-256)</span>
            </div>
          </div>

          {/* Role Selector Tabs (Auditor, Analista, Administrador) */}
          <div className="mb-5 p-1 rounded-xl bg-[#0a0e18]/80 border border-white/10 grid grid-cols-3 gap-1 text-center">
            {(['auditor', 'analista', 'admin'] as UserRole[]).map((role) => {
              const isSelected = selectedRole === role;
              const info = roleCredentialsMap[role];
              return (
                <button
                  key={role}
                  type="button"
                  onClick={() => handleSelectRoleTab(role)}
                  className={`py-1.5 px-2 rounded-lg text-xs font-semibold transition-all flex flex-col items-center justify-center gap-0.5 ${
                    isSelected
                      ? 'bg-[#4f46e5] text-white shadow-md'
                      : 'text-slate-400 hover:text-white hover:bg-[#171b26]'
                  }`}
                >
                  <span className="truncate">{info.label}</span>
                  <span className={`text-[9px] font-mono ${isSelected ? 'text-indigo-200' : 'text-slate-500'}`}>
                    {role === 'auditor' ? 'Nivel 4' : role === 'analista' ? 'Nivel 2' : 'Nivel 5'}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Error Banner */}
          {errorMsg && (
            <div className="mb-4 p-3 rounded-xl bg-red-950/60 border border-red-500/40 text-xs text-red-200 flex items-center gap-2 animate-fade-in">
              <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Form */}
          <form className="space-y-4" onSubmit={handleFormSubmit}>
            
            {/* Input 1: User / Email with avatar circle */}
            <div className="relative flex items-center">
              <div className="absolute left-1.5 z-10 w-10 h-10 rounded-full bg-[#262a35] border border-white/10 flex items-center justify-center text-indigo-300 shadow-md">
                <User className="w-4 h-4" />
              </div>
              <input
                type="text"
                value={emailInput}
                onChange={(e) => setEmailInput(e.target.value)}
                placeholder="auditor.soberano@enclave.aduana.gob"
                required
                className="w-full bg-[#090d16]/80 border border-white/15 pl-14 pr-4 py-3.5 rounded-full text-xs text-[#dfe2f1] placeholder:text-slate-500 focus:outline-none focus:border-indigo-400 focus:ring-1 focus:ring-indigo-400 transition-all font-sans"
              />
            </div>

            {/* Input 2: Password / Passkey with lock circle */}
            <div className="relative flex items-center">
              <input
                id="password-input"
                type={showPassword ? 'text' : 'password'}
                value={passwordInput}
                onChange={(e) => setPasswordInput(e.target.value)}
                placeholder="Passkey o Clave Encriptada"
                required
                className="w-full bg-[#090d16]/80 border border-white/15 pl-5 pr-14 py-3.5 rounded-full text-xs text-[#dfe2f1] placeholder:text-slate-500 focus:outline-none focus:border-indigo-400 focus:ring-1 focus:ring-indigo-400 font-mono tracking-wider transition-all"
              />
              <button
                type="button"
                id="toggle-password"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-1.5 z-10 w-10 h-10 rounded-full bg-[#262a35] border border-white/10 flex items-center justify-center text-indigo-300 shadow-md cursor-pointer hover:bg-[#313540] transition-colors"
                title={showPassword ? 'Ocultar passkey' : 'Mostrar passkey'}
              >
                {showPassword ? <Unlock className="w-4 h-4 text-emerald-400" /> : <Lock className="w-4 h-4" />}
              </button>
            </div>

            {/* Remember Node & Forgot Link */}
            <div className="flex items-center justify-between px-2 pt-1 text-xs">
              <label className="inline-flex items-center space-x-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={rememberNode}
                  onChange={(e) => setRememberNode(e.target.checked)}
                  className="w-4 h-4 rounded border-white/20 bg-[#0a0e18] text-indigo-600 focus:ring-0 focus:ring-offset-0 cursor-pointer"
                />
                <span className="text-[#c7c4d8] hover:text-white transition-colors text-xs font-sans">
                  Recordar nodo seguro
                </span>
              </label>

              <button
                type="button"
                onClick={() => setShowForgotModal(true)}
                className="text-xs text-[#c3c0ff] hover:text-white transition-colors hover:underline font-sans"
              >
                ¿Olvidó su Passkey?
              </button>
            </div>

            {/* Submit Button (INICIAR SESIÓN SEGURA ->) */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={isAuthenticating}
                className="w-full py-3.5 sm:py-4 px-6 rounded-full bg-[#dfe2f1] text-[#0a0e18] font-bold text-xs sm:text-sm tracking-wider hover:bg-white hover:shadow-[0_0_24px_rgba(255,255,255,0.4)] active:scale-[0.99] transition-all duration-150 flex items-center justify-center space-x-2 cursor-pointer disabled:opacity-70"
              >
                <span>{isAuthenticating ? 'VALIDANDO EN ENCLAVE...' : 'INICIAR SESIÓN SEGURA'}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>

          </form>

          {/* Bottom Telemetry Footer */}
          <div className="mt-6 pt-5 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between text-xs text-[#c7c4d8] font-mono">
            <div className="flex items-center space-x-2 mb-2 sm:mb-0">
              <CheckCircle2 className="w-4 h-4 text-[#4edea3]" />
              <span className="text-[11px]">Hardware Token PKCS#11 Detectado</span>
            </div>

            <button
              type="button"
              onClick={() => setShowHardwareTokenModal(true)}
              className="text-[#adc6ff] hover:text-white text-[11px] transition-colors hover:underline flex items-center space-x-1"
            >
              <span>Verificar Firma de Nodo</span>
              <ExternalLink className="w-3 h-3" />
            </button>
          </div>

        </div>

      </main>

      {/* Hardware Token Verification Modal */}
      {showHardwareTokenModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-md bg-[#0d1527] border border-indigo-500/40 rounded-2xl p-6 shadow-2xl space-y-4 text-white">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
                <h3 className="text-sm font-bold">Verificación Criptográfica de Nodo</h3>
              </div>
              <button 
                onClick={() => setShowHardwareTokenModal(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs font-mono text-slate-300">
              <div className="p-3 rounded-xl bg-[#090d16] border border-white/10 space-y-1">
                <span className="text-slate-400 text-[10px]">Identificador de Nodo:</span>
                <p className="text-emerald-400 font-bold">NODO-SOBERANO-VE-CARACAS-01</p>
              </div>

              <div className="p-3 rounded-xl bg-[#090d16] border border-white/10 space-y-1">
                <span className="text-slate-400 text-[10px]">Módulo Criptográfico:</span>
                <p>HSM PKCS#11 FIPS 140-3 Level 4 Compliant</p>
              </div>

              <div className="p-3 rounded-xl bg-[#090d16] border border-white/10 space-y-1">
                <span className="text-slate-400 text-[10px]">Hash de Consenso Activo:</span>
                <p className="text-indigo-300 break-all text-[10px]">
                  0xe3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
                </p>
              </div>
            </div>

            <button
              onClick={() => setShowHardwareTokenModal(false)}
              className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs transition-colors"
            >
              Cerrar Diagnóstico
            </button>
          </div>
        </div>
      )}

      {/* Forgot Passkey Modal with Pre-configured Presets */}
      {showForgotModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-md bg-[#0d1527] border border-indigo-500/40 rounded-2xl p-6 shadow-2xl space-y-4 text-white">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div className="flex items-center gap-2">
                <KeyRound className="w-5 h-5 text-amber-400" />
                <h3 className="text-sm font-bold">Credenciales Oficiales de Demostración</h3>
              </div>
              <button 
                onClick={() => setShowForgotModal(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-2 text-xs">
              <p className="text-slate-300 leading-relaxed text-[11px]">
                En este entorno soberano, las claves de acceso de prueba están pre-cargadas en el enclave:
              </p>

              {(['auditor', 'analista', 'admin'] as UserRole[]).map((r) => {
                const item = roleCredentialsMap[r];
                return (
                  <div key={r} className="p-2.5 rounded-xl bg-[#090d16] border border-white/10 font-mono text-[11px] space-y-0.5">
                    <div className="flex items-center justify-between text-indigo-300 font-bold">
                      <span>{item.label} ({item.clearance}):</span>
                      <button
                        onClick={() => {
                          handleSelectRoleTab(r);
                          setShowForgotModal(false);
                        }}
                        className="text-emerald-400 hover:underline text-[10px]"
                      >
                        Cargar
                      </button>
                    </div>
                    <div className="text-slate-400">Usuario: <span className="text-white">{item.email}</span></div>
                    <div className="text-slate-400">Clave: <span className="text-white font-bold">{item.pass}</span></div>
                  </div>
                );
              })}
            </div>

            <button
              onClick={() => setShowForgotModal(false)}
              className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs transition-colors"
            >
              Entendido
            </button>
          </div>
        </div>
      )}

    </div>
  );
};
