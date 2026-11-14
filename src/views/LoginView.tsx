import React, { useState, useEffect, useRef } from 'react';
import { 
  Lock, 
  Unlock, 
  User, 
  ArrowRight, 
  AlertCircle,
  KeyRound,
  X
} from 'lucide-react';
import { AuthUser, UserRole } from '../types/auth';
import { MOCK_AUTH_USERS } from '../constants/mockAuth';
import loginBgImg from '../assets/login-bg.jpg';
import systemLogoImg from '../assets/Logo-white.png';

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
  const [emailInput, setEmailInput] = useState<string>('auditor.soberano@enclave.aduana.gob');
  const [passwordInput, setPasswordInput] = useState<string>('auditor2026');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberNode, setRememberNode] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [showForgotModal, setShowForgotModal] = useState(false);

  // Parallax animation refs from code.html & DESIGN.md
  const bgRef = useRef<HTMLImageElement>(null);
  const cardRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) return;

    let targetX = 0, targetY = 0;
    let currentX = 0, currentY = 0;
    let animationFrameId: number | null = null;

    const updateCardMouseCoords = (clientX: number, clientY: number) => {
      if (!cardRef.current) return;
      const rect = cardRef.current.getBoundingClientRect();
      const cardX = ((clientX - rect.left) / rect.width) * 100;
      const cardY = ((clientY - rect.top) / rect.height) * 100;
      cardRef.current.style.setProperty('--mouse-x', `${cardX}%`);
      cardRef.current.style.setProperty('--mouse-y', `${cardY}%`);
    };

    const animateLoop = () => {
      // Smooth lerp (momentum easing)
      const lerpFactor = 0.08;
      currentX += (targetX - currentX) * lerpFactor;
      currentY += (targetY - currentY) * lerpFactor;

      // Background parallax counter-translation
      if (bgRef.current) {
        const bgTranslateX = -currentX * 32;
        const bgTranslateY = -currentY * 32;
        bgRef.current.style.transform = `scale(1.1) translate3d(${bgTranslateX.toFixed(2)}px, ${bgTranslateY.toFixed(2)}px, 0)`;
      }

      // Card tilt & perspective translation
      if (cardRef.current) {
        const cardTranslateX = currentX * 16;
        const cardTranslateY = currentY * 16;
        const cardRotateY = currentX * 7.5;
        const cardRotateX = -currentY * 7.5;
        cardRef.current.style.transform = `translate3d(${cardTranslateX.toFixed(2)}px, ${cardTranslateY.toFixed(2)}px, 0) rotateX(${cardRotateX.toFixed(2)}deg) rotateY(${cardRotateY.toFixed(2)}deg)`;
      }

      animationFrameId = requestAnimationFrame(animateLoop);
    };

    const handleMouseMove = (e: MouseEvent) => {
      const { innerWidth: width, innerHeight: height } = window;
      targetX = (e.clientX / width) - 0.5; // -0.5 to 0.5
      targetY = (e.clientY / height) - 0.5; // -0.5 to 0.5

      updateCardMouseCoords(e.clientX, e.clientY);

      if (!animationFrameId) {
        animationFrameId = requestAnimationFrame(animateLoop);
      }
    };

    const handleMouseLeave = () => {
      targetX = 0;
      targetY = 0;
      if (cardRef.current) {
        cardRef.current.style.setProperty('--mouse-x', '50%');
        cardRef.current.style.setProperty('--mouse-y', '50%');
      }
    };

    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    document.body.addEventListener('mouseleave', handleMouseLeave);

    // Initial animation loop start
    animationFrameId = requestAnimationFrame(animateLoop);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      document.body.removeEventListener('mouseleave', handleMouseLeave);
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
      }
    };
  }, []);

  const demoAccounts: { role: UserRole; label: string; email: string; pass: string; clearance: string }[] = [
    {
      role: 'auditor',
      label: 'Auditor (Deykary González)',
      email: 'auditor.soberano@enclave.aduana.gob',
      pass: 'auditor2026',
      clearance: 'Nivel 4 — Confidencial Estatal'
    },
    {
      role: 'analista',
      label: 'Analista (Elena Salazar)',
      email: 'analista.operaciones@enclave.aduana.gob',
      pass: 'analista2026',
      clearance: 'Nivel 2 — Operativo Aduanero'
    },
    {
      role: 'admin',
      label: 'Administrador (Marcos Vivas)',
      email: 'admin.infraestructura@enclave.aduana.gob',
      pass: 'admin2026',
      clearance: 'Nivel 5 — Soberanía Crítica'
    }
  ];

  const handleSelectAccount = (acc: typeof demoAccounts[0]) => {
    setEmailInput(acc.email);
    setPasswordInput(acc.pass);
    setShowForgotModal(false);
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

      if (emailClean.includes('analista')) {
        matchedUser = MOCK_AUTH_USERS.analista;
      } else if (emailClean.includes('admin')) {
        matchedUser = MOCK_AUTH_USERS.admin;
      } else {
        // Default to auditor
        matchedUser = MOCK_AUTH_USERS.auditor;
      }

      if (!matchedUser) {
        setErrorMsg('Credencial no registrada en el enclave del nodo local.');
        setIsAuthenticating(false);
        return;
      }

      setIsAuthenticating(false);
      onLogin(matchedUser);
    }, 400);
  };

  return (
    <div className="relative min-h-screen flex flex-col justify-center items-center bg-[#0f131d] text-[#dfe2f1] overflow-x-hidden selection:bg-indigo-600 selection:text-white select-none">
      
      {/* Ambient Cinematic Deep Background with Cryptographic NOC Mesh & Parallax */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        <img 
          ref={bgRef}
          alt="Aduana IA Control Center" 
          src={loginBgImg} 
          className="parallax-layer-bg w-full h-full object-cover object-center opacity-30 filter brightness-[0.45] contrast-125 scale-105"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-[#0f131d] via-[#0f131d]/85 to-transparent" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(79,70,229,0.22)_0%,transparent_70%)]" />
        <div className="absolute inset-0 cyber-scanline pointer-events-none" />
      </div>

      {/* Main Login Canvas / 3D Perspective Tilt Container */}
      <main className="relative z-10 w-full max-w-[480px] px-4 py-8 mx-auto flex flex-col items-center card-perspective-container">
        
        {/* Glass Specimen Card with Dynamic Specular Highlight & Parallax Tilt */}
        <div 
          ref={cardRef}
          className="w-full rounded-2xl p-6 sm:p-8 backdrop-blur-2xl border border-indigo-500/30 relative overflow-hidden transition-all duration-300 card-parallax-tilt neon-border-glow"
          style={{
            background: 'radial-gradient(circle 380px at var(--mouse-x, 50%) var(--mouse-y, 50%), rgba(255, 255, 255, 0.08), transparent 80%), rgba(13, 21, 39, 0.82)'
          }}
        >
          
          {/* Top Hairline Gradient Accent */}
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-[#4f46e5] to-transparent opacity-85" />

          {/* Card Header */}
          <div className="text-center mb-6">
            {/* Official System Emblem Logo */}
            <div className="inline-flex items-center justify-center mb-3">
              <img 
                src={systemLogoImg} 
                alt="Aduana IA" 
                className="w-20 h-20 sm:w-24 sm:h-24 object-contain drop-shadow-[0_4px_16px_rgba(0,0,0,0.6)] drop-shadow-[0_0_24px_rgba(79,70,229,0.35)] transition-transform duration-300 hover:scale-105"
              />
            </div>

            <h1 className="text-2xl sm:text-[28px] font-bold text-white tracking-tight">
              Acceso Criptográfico
            </h1>
            <p className="text-xs text-[#c7c4d8] mt-1 font-sans">
              Infraestructura Crítica de Control Fronterizo y Aduanal
            </p>
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
                autoComplete="off"
                value={emailInput}
                onChange={(e) => setEmailInput(e.target.value)}
                placeholder="auditor.soberano@enclave.aduana.gob"
                required
                className="w-full bg-[#090d16]/80 border border-white/15 pl-14 pr-4 py-3.5 rounded-full text-xs sm:text-sm text-[#dfe2f1] placeholder:text-slate-500 focus:outline-none focus:border-indigo-400 focus:ring-1 focus:ring-indigo-400 transition-all font-sans"
              />
            </div>

            {/* Input 2: Password / Passkey with lock circle */}
            <div className="relative flex items-center">
              <input
                id="password-input"
                type={showPassword ? 'text' : 'password'}
                autoComplete="off"
                value={passwordInput}
                onChange={(e) => setPasswordInput(e.target.value)}
                placeholder="Passkey o Clave Encriptada"
                required
                className="w-full bg-[#090d16]/80 border border-white/15 pl-5 pr-14 py-3.5 rounded-full text-xs sm:text-sm text-[#dfe2f1] placeholder:text-slate-500 focus:outline-none focus:border-indigo-400 focus:ring-1 focus:ring-indigo-400 font-mono tracking-wider transition-all"
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
                  autoComplete="off"
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
                className="w-full py-3.5 sm:py-4 px-6 rounded-full bg-[#dfe2f1] text-[#0a0e18] font-bold text-xs sm:text-sm tracking-wider hover:bg-white hover:shadow-[0_0_24px_rgba(255,255,255,0.4)] active:scale-[0.99] transition-all duration-150 flex items-center justify-center space-x-2 cursor-pointer disabled:opacity-70 shimmer-btn"
              >
                <span>{isAuthenticating ? 'VALIDANDO EN ENCLAVE...' : 'INICIAR SESIÓN SEGURA'}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>

          </form>

        </div>

      </main>

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
                Seleccione una de las credenciales de demostración para cargarla en el formulario:
              </p>

              {demoAccounts.map((acc) => (
                <div key={acc.role} className="p-2.5 rounded-xl bg-[#090d16] border border-white/10 font-mono text-[11px] space-y-0.5">
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
                  <div className="text-slate-400">Usuario: <span className="text-white">{acc.email}</span></div>
                  <div className="text-slate-400">Passkey: <span className="text-white font-bold">{acc.pass}</span></div>
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
