import React, { useEffect, useState } from 'react';
import {
  Shield,
  Lock,
  Unlock,
  User,
  ArrowRight,
  Sun,
  Moon,
  AlertCircle,
  KeyRound,
  X,
} from 'lucide-react';
import { AuthUser, UserRole } from '../types/auth';
import { api, errorMessage } from '../services/apiClient';
import loginBgImg from '../assets/login-bg.jpg';

interface LoginViewProps {
  onLogin: (user: AuthUser, sessionToken: string) => void;
  darkMode: boolean;
  onToggleDarkMode: () => void;
}

export const LoginView: React.FC<LoginViewProps> = ({
  onLogin,
  darkMode,
  onToggleDarkMode,
}) => {
  const [cedulaInput, setCedulaInput] = useState<string>('');
  const [passwordInput, setPasswordInput] = useState<string>('');
  const [showPassword, setShowPassword] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [showForgotModal, setShowForgotModal] = useState(false);

  // Zero-Trust: limpiar credenciales sensibles en memoria RAM al desmontar la vista
  useEffect(() => {
    return () => {
      setCedulaInput('');
      setPasswordInput('');
      setErrorMsg(null);
      setShowPassword(false);
    };
  }, []);

  const demoAccounts: {
    role: UserRole;
    label: string;
    cedula: string;
    pass: string;
    clearance: string;
  }[] = [
    {
      role: 'auditor',
      label: 'Auditor (Deykary González)',
      cedula: 'V-14220101',
      pass: 'auditor2026',
      clearance: 'Nivel 4 — Confidencial Estatal',
    },
    {
      role: 'analista',
      label: 'Analista (Elena Salazar)',
      cedula: 'V-18660505',
      pass: 'analista2026',
      clearance: 'Nivel 2 — Operativo Aduanero',
    },
    {
      role: 'administrador',
      label: 'Administrador (Marcos Vivas)',
      cedula: 'V-12110909',
      pass: 'admin2026',
      clearance: 'Nivel 5 — Soberanía Crítica',
    },
  ];

  const handleSelectAccount = (acc: (typeof demoAccounts)[0]) => {
    setCedulaInput(acc.cedula);
    setPasswordInput(acc.pass);
    setShowForgotModal(false);
    setErrorMsg(null);
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setIsAuthenticating(true);

    try {
      const res = await api.login({
        cedula: cedulaInput.trim(),
        password: passwordInput,
      });

      const hydratedUser: AuthUser = {
        id: res.user.id,
        name: res.user.full_name,
        shortName: res.user.short_name,
        role: res.user.role,
        roleLabel: res.user.role_label,
        avatarText: res.user.avatar_text,
        email: `${res.user.username}@aduana.gob.ve`,
        status: 'online',
        credentials: {
          clearanceLevel: res.user.clearance_level,
          entity: res.user.entity,
          ed25519Key: 'Enclave-RAM',
          ed25519Status: 'Validada y Activa',
          permissions: res.user.permissions,
          sessionId: res.citizen_receipt_code,
          fingerprint: `ledger-block:#${res.block_index}`,
          department: res.user.department,
          idNumber: res.user.id,
        },
        lastLogin: new Date().toISOString(),
      };

      // Limpiar inputs en memoria antes de transferir sesión
      setCedulaInput('');
      setPasswordInput('');
      onLogin(hydratedUser, res.session_token);
    } catch (err) {
      setErrorMsg(errorMessage(err));
    } finally {
      setIsAuthenticating(false);
    }
  };

  return (
    <div className="relative min-h-screen flex flex-col justify-center items-center bg-[#0f131d] text-[#dfe2f1] overflow-x-hidden selection:bg-indigo-600 selection:text-white select-none">
      {/* Ambient Cinematic Deep Background with Cryptographic NOC Mesh */}
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
          {darkMode ? (
            <Sun className="w-4 h-4 text-amber-400" />
          ) : (
            <Moon className="w-4 h-4 text-indigo-400" />
          )}
        </button>
      </div>

      {/* Main Login Canvas / Glass Enclave Container */}
      <main className="relative z-10 w-full max-w-[480px] px-4 py-8 mx-auto flex flex-col items-center">
        <div className="w-full rounded-2xl p-6 sm:p-8 backdrop-blur-2xl bg-[#0d1527]/80 border border-indigo-500/30 shadow-[0_0_35px_-4px_rgba(79,70,229,0.35)] relative overflow-hidden transition-all duration-300">
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-[#4f46e5] to-transparent opacity-85" />

          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center p-3 rounded-2xl bg-[#171b26] border border-indigo-500/40 mb-3 shadow-[0_0_22px_rgba(79,70,229,0.35)] text-indigo-400">
              <Shield className="w-8 h-8 fill-indigo-400/20 stroke-indigo-400" />
            </div>

            <h1 className="text-2xl sm:text-[28px] font-bold text-white tracking-tight">
              Acceso Criptográfico
            </h1>
            <p className="text-xs text-[#c7c4d8] mt-1 font-sans">
              Infraestructura Crítica de Control Fronterizo y Aduanal
            </p>

            <div className="inline-flex items-center space-x-1.5 mt-3 px-3 py-1 rounded-full bg-[#0a0e18]/85 border border-white/10 text-[11px] font-mono text-[#4edea3]">
              <span className="w-2 h-2 rounded-full bg-[#4edea3] animate-pulse" />
              <span>Zero-Trust Enclave (PBKDF2-HMAC-SHA256 / RAM-Only)</span>
            </div>
          </div>

          {errorMsg && (
            <div className="mb-4 p-3 rounded-xl bg-red-950/60 border border-red-500/40 text-xs text-red-200 flex items-center gap-2 animate-fade-in">
              <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          <form className="space-y-4" onSubmit={handleFormSubmit} autoComplete="off">
            {/* Input 1: Cédula de Identidad (V-/E-) */}
            <div className="relative flex items-center">
              <div className="absolute left-1.5 z-10 w-10 h-10 rounded-full bg-[#262a35] border border-white/10 flex items-center justify-center text-indigo-300 shadow-md">
                <User className="w-4 h-4" />
              </div>
              <input
                id="cedula-input"
                type="text"
                autoComplete="off"
                spellCheck={false}
                value={cedulaInput}
                onChange={(e) => setCedulaInput(e.target.value)}
                placeholder="Cédula de Identidad (ej. V-14220101)"
                required
                className="w-full bg-[#090d16]/80 border border-white/15 pl-14 pr-4 py-3.5 rounded-full text-xs sm:text-sm text-[#dfe2f1] placeholder:text-slate-500 focus:outline-none focus:border-indigo-400 focus:ring-1 focus:ring-indigo-400 transition-all font-mono"
              />
            </div>

            {/* Input 2: Contraseña PBKDF2 */}
            <div className="relative flex items-center">
              <input
                id="password-input"
                type={showPassword ? 'text' : 'password'}
                autoComplete="off"
                spellCheck={false}
                value={passwordInput}
                onChange={(e) => setPasswordInput(e.target.value)}
                placeholder="Contraseña de Funcionario"
                required
                className="w-full bg-[#090d16]/80 border border-white/15 pl-5 pr-14 py-3.5 rounded-full text-xs sm:text-sm text-[#dfe2f1] placeholder:text-slate-500 focus:outline-none focus:border-indigo-400 focus:ring-1 focus:ring-indigo-400 font-mono tracking-wider transition-all"
              />
              <button
                type="button"
                id="toggle-password"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-1.5 z-10 w-10 h-10 rounded-full bg-[#262a35] border border-white/10 flex items-center justify-center text-indigo-300 shadow-md cursor-pointer hover:bg-[#313540] transition-colors"
                title={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
              >
                {showPassword ? (
                  <Unlock className="w-4 h-4 text-emerald-400" />
                ) : (
                  <Lock className="w-4 h-4" />
                )}
              </button>
            </div>

            <div className="flex items-center justify-between px-2 pt-1 text-xs">
              <span className="text-[#c7c4d8] text-[11px] font-mono">
                Sesión efímera en RAM (sin Storage)
              </span>
              <button
                type="button"
                onClick={() => setShowForgotModal(true)}
                className="text-xs text-[#c3c0ff] hover:text-white transition-colors hover:underline font-sans"
              >
                Credenciales Demo
              </button>
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={isAuthenticating}
                className="w-full py-3.5 sm:py-4 px-6 rounded-full bg-[#dfe2f1] text-[#0a0e18] font-bold text-xs sm:text-sm tracking-wider hover:bg-white hover:shadow-[0_0_24px_rgba(255,255,255,0.4)] active:scale-[0.99] transition-all duration-150 flex items-center justify-center space-x-2 cursor-pointer disabled:opacity-70"
              >
                <span>
                  {isAuthenticating ? 'VALIDANDO EN ENCLAVE...' : 'INICIAR SESIÓN SEGURA'}
                </span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </form>
        </div>
      </main>

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
                Seleccione una de las credenciales para cargarla en el formulario:
              </p>

              {demoAccounts.map((acc) => (
                <div
                  key={acc.role}
                  className="p-2.5 rounded-xl bg-[#090d16] border border-white/10 font-mono text-[11px] space-y-0.5"
                >
                  <div className="flex items-center justify-between text-indigo-300 font-bold">
                    <span>{acc.label}:</span>
                    <button
                      type="button"
                      onClick={() => handleSelectAccount(acc)}
                      className="px-2 py-0.5 rounded-md bg-indigo-600 hover:bg-indigo-500 text-white font-sans text-[10px] transition-colors"
                    >
                      Cargar
                    </button>
                  </div>
                  <div className="text-slate-400">
                    Cédula: <span className="text-white">{acc.cedula}</span>
                  </div>
                  <div className="text-slate-400">
                    Clave: <span className="text-white font-bold">{acc.pass}</span>
                  </div>
                </div>
              ))}
            </div>

            <button
              type="button"
              onClick={() => setShowForgotModal(false)}
              className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs transition-colors"
            >
              Cerrar
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
