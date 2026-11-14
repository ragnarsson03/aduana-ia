import React, { useState } from 'react';
import { 
  ShieldCheck, 
  KeyRound, 
  Building2, 
  Lock, 
  CheckCircle2, 
  FileCheck, 
  Settings, 
  LogOut, 
  User, 
  Sun, 
  Moon, 
  History, 
  Copy, 
  RefreshCw, 
  ArrowLeft,
  Sliders,
  BellRing
} from 'lucide-react';
import { AuthUser } from '../types/auth';
import { NavTabId } from '../types/navigation';
import { ROLE_ALLOWED_TABS, ROLE_DEFAULT_TAB } from '../constants/mockAuth';

interface ProfileViewProps {
  user: AuthUser;
  darkMode: boolean;
  onToggleDarkMode: () => void;
  onLogout: () => void;
  onNavigate: (tab: NavTabId) => void;
  defaultSection?: 'profile' | 'settings';
}

export const ProfileView: React.FC<ProfileViewProps> = ({
  user,
  darkMode,
  onToggleDarkMode,
  onLogout,
  onNavigate,
  defaultSection = 'profile'
}) => {
  const [activeTab, setActiveTab] = useState<'profile' | 'settings' | 'security'>(defaultSection);
  const [copiedKey, setCopiedKey] = useState(false);
  const [autoMaskPII, setAutoMaskPII] = useState(true);
  const [ledgerAuditNotify, setLedgerAuditNotify] = useState(true);
  const [rotatedKeyMessage, setRotatedKeyMessage] = useState<string | null>(null);

  const creds = user.credentials;

  const handleCopyKey = () => {
    navigator.clipboard.writeText(creds.ed25519Key);
    setCopiedKey(true);
    setTimeout(() => setCopiedKey(false), 2000);
  };

  const handleRotateKey = () => {
    setRotatedKeyMessage('Nueva clave efímera Ed25519 generada y sellada en memoria confinada.');
    setTimeout(() => setRotatedKeyMessage(null), 4000);
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      {/* Top Breadcrumb & Return Action */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => onNavigate(ROLE_DEFAULT_TAB[user.role] || 'ledger')}
          className="inline-flex items-center gap-2 text-xs font-semibold text-neutral-500 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Volver al Panel Principal ({user.role === 'auditor' ? 'Ledger' : 'Pasarela'})</span>
        </button>

        <div className="flex items-center gap-2">
          <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 font-medium border border-emerald-200/50 dark:border-emerald-800/40 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            Enclave Criptográfico Activo
          </span>
        </div>
      </div>

      {/* Main Profile Header Banner */}
      <div className="relative rounded-2xl bg-gradient-to-r from-indigo-900/90 via-indigo-950 to-slate-950 border border-indigo-500/30 p-6 sm:p-8 text-white shadow-xl overflow-hidden">
        <div className="absolute top-0 right-0 -mr-16 -mt-16 w-64 h-64 rounded-full bg-primary/20 blur-3xl pointer-events-none" />
        
        <div className="relative z-10 flex flex-col sm:flex-row items-center sm:items-start gap-6 text-center sm:text-left">
          {/* Avatar Box */}
          <div className="relative shrink-0">
            <div className="w-24 h-24 rounded-2xl bg-[#141b29] text-indigo-300 font-bold text-3xl flex items-center justify-center border-2 border-indigo-500/40 shadow-xl">
              {user.avatarText}
            </div>
            <span className="w-4 h-4 rounded-full bg-emerald-500 absolute -bottom-1 -right-1 ring-4 ring-[#0b0f19]" />
          </div>

          {/* User Info */}
          <div className="flex-1 min-w-0 space-y-2">
            <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2.5">
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
                {user.name}
              </h1>
              <span className="px-3 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/30 text-indigo-200 border border-indigo-400/30">
                {user.roleLabel}
              </span>
            </div>

            <p className="text-sm font-mono text-indigo-300/80">
              {creds.idNumber} • {user.email}
            </p>

            <div className="flex flex-wrap items-center justify-center sm:justify-start gap-4 pt-1 text-xs text-indigo-200/70 font-mono">
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                Credenciales Verificadas por Aduana IA
              </span>
              <span>•</span>
              <span>Sesión: {creds.sessionId}</span>
              {user.lastLogin && (
                <>
                  <span>•</span>
                  <span>Último acceso: {user.lastLogin}</span>
                </>
              )}
            </div>
          </div>

          {/* Logout Action in Banner */}
          <div className="shrink-0 pt-2 sm:pt-0">
            <button
              onClick={onLogout}
              className="px-4 py-2 rounded-xl text-xs font-semibold bg-red-600/90 hover:bg-red-700 text-white transition-all shadow-sm active:scale-95 flex items-center gap-2 border border-red-500/40"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Cerrar sesión</span>
            </button>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-neutral-200 dark:border-neutral-800 pb-2">
        <button
          onClick={() => setActiveTab('profile')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'profile'
              ? 'bg-primary text-white shadow-sm'
              : 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800'
          }`}
        >
          <User className="w-3.5 h-3.5" />
          <span>Credenciales e Institucionales</span>
        </button>

        <button
          onClick={() => setActiveTab('settings')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'settings'
              ? 'bg-primary text-white shadow-sm'
              : 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800'
          }`}
        >
          <Settings className="w-3.5 h-3.5" />
          <span>Ajustes del Sistema</span>
        </button>

        <button
          onClick={() => setActiveTab('security')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'security'
              ? 'bg-primary text-white shadow-sm'
              : 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800'
          }`}
        >
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Enclave Criptográfico & Llaves</span>
        </button>
      </div>

      {/* Tab 1: Credenciales e Institucionales (Matches Image 2) */}
      {activeTab === 'profile' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-fade-in">
          {/* Card: Credenciales Oficiales */}
          <div className="p-6 rounded-2xl bg-white dark:bg-[#0c121e] border border-neutral-200 dark:border-neutral-800 shadow-sm space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-neutral-100 dark:border-neutral-800/80">
              <h2 className="text-sm font-bold text-neutral-900 dark:text-white uppercase tracking-wider">
                Credenciales e Institucionales
              </h2>
              <span className="text-xs font-mono text-emerald-600 dark:text-emerald-400 font-semibold">
                ● VIGENTE
              </span>
            </div>

            {/* Nivel de Clearance */}
            <div className="p-4 rounded-xl bg-neutral-50 dark:bg-[#111827] border border-neutral-200/80 dark:border-neutral-800/80 space-y-1">
              <div className="flex items-center gap-2 text-xs font-mono text-neutral-500 dark:text-neutral-400">
                <Lock className="w-3.5 h-3.5 text-indigo-500" />
                <span>Nivel de Clearance:</span>
              </div>
              <p className="text-sm font-bold text-neutral-900 dark:text-white pl-5">
                {creds.clearanceLevel}
              </p>
            </div>

            {/* Entidad / Unidad */}
            <div className="p-4 rounded-xl bg-neutral-50 dark:bg-[#111827] border border-neutral-200/80 dark:border-neutral-800/80 space-y-1">
              <div className="flex items-center gap-2 text-xs font-mono text-neutral-500 dark:text-neutral-400">
                <Building2 className="w-3.5 h-3.5 text-emerald-500" />
                <span>Entidad / Unidad:</span>
              </div>
              <p className="text-sm font-semibold text-neutral-900 dark:text-white pl-5">
                {creds.entity}
              </p>
              {creds.department && (
                <p className="text-xs text-neutral-500 dark:text-neutral-400 pl-5">
                  {creds.department}
                </p>
              )}
            </div>

            {/* Firma Criptográfica Ed25519 */}
            <div className="p-4 rounded-xl bg-neutral-50 dark:bg-[#111827] border border-neutral-200/80 dark:border-neutral-800/80 space-y-1.5">
              <div className="flex items-center justify-between text-xs font-mono text-neutral-500 dark:text-neutral-400">
                <div className="flex items-center gap-2">
                  <KeyRound className="w-3.5 h-3.5 text-amber-500" />
                  <span>Firma Criptográfica Ed25519:</span>
                </div>
                <span className="text-emerald-600 dark:text-emerald-400 font-bold">
                  {creds.ed25519Status}
                </span>
              </div>
              <div className="flex items-center justify-between pl-5 bg-white dark:bg-[#0c121e] p-2 rounded-lg border border-neutral-200 dark:border-neutral-800">
                <span className="text-xs font-mono text-neutral-800 dark:text-neutral-200">
                  {creds.ed25519Key}
                </span>
                <button
                  onClick={handleCopyKey}
                  className="text-xs text-indigo-500 hover:text-indigo-600 flex items-center gap-1 font-sans"
                >
                  <Copy className="w-3 h-3" />
                  <span>{copiedKey ? 'Copiado' : 'Copiar'}</span>
                </button>
              </div>
            </div>

            {/* Permisos de Acceso */}
            <div className="p-4 rounded-xl bg-neutral-50 dark:bg-[#111827] border border-neutral-200/80 dark:border-neutral-800/80 space-y-2">
              <div className="flex items-center gap-2 text-xs font-mono text-neutral-500 dark:text-neutral-400">
                <FileCheck className="w-3.5 h-3.5 text-primary" />
                <span>Permisos de Acceso Autorizados:</span>
              </div>
              <ul className="space-y-1.5 pl-5">
                {creds.permissions.map((perm, idx) => (
                  <li key={idx} className="text-xs text-neutral-700 dark:text-neutral-300 flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" />
                    <span>{perm}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Zero Trust Footer */}
            <div className="p-3 text-center rounded-xl bg-indigo-50/60 dark:bg-indigo-950/20 border border-indigo-200/50 dark:border-indigo-800/40">
              <p className="text-[11px] font-mono text-indigo-700 dark:text-indigo-300 font-semibold uppercase tracking-wider">
                Canal Soberano Segregado • Protocolo Zero-Trust
              </p>
            </div>
          </div>

          {/* Card: Estado del Nodo y Verificación */}
          <div className="space-y-6">
            <div className="p-6 rounded-2xl bg-white dark:bg-[#0c121e] border border-neutral-200 dark:border-neutral-800 shadow-sm space-y-5">
              <div className="flex items-center justify-between pb-3 border-b border-neutral-100 dark:border-neutral-800/80">
                <h3 className="text-sm font-bold text-neutral-900 dark:text-white uppercase tracking-wider">
                  Verificación de Enclave Local
                </h3>
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 font-mono font-medium border border-indigo-200/50 dark:border-indigo-800/40">
                  Gov-Ed25519
                </span>
              </div>

              <div className="space-y-3 text-xs">
                <div className="flex items-center justify-between p-3 rounded-xl bg-neutral-50 dark:bg-[#111827]">
                  <span className="text-neutral-500 dark:text-neutral-400">Huella Criptográfica SHA-256:</span>
                  <span className="font-mono text-neutral-800 dark:text-neutral-200 font-semibold">{creds.fingerprint}</span>
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl bg-neutral-50 dark:bg-[#111827]">
                  <span className="text-neutral-500 dark:text-neutral-400">Cumplimiento Normativo:</span>
                  <span className="font-semibold text-emerald-600 dark:text-emerald-400">ISO/IEC 27001 • ENISA Gov-AI</span>
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl bg-neutral-50 dark:bg-[#111827]">
                  <span className="text-neutral-500 dark:text-neutral-400">Nodo de Asignación:</span>
                  <span className="font-mono text-neutral-800 dark:text-neutral-200 font-medium">Nodo Soberano #01 (Caracas)</span>
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl bg-neutral-50 dark:bg-[#111827]">
                  <span className="text-neutral-500 dark:text-neutral-400">Persistencia de Ledger:</span>
                  <span className="font-medium text-neutral-800 dark:text-neutral-200">100% Local-First Confinado</span>
                </div>
              </div>

              <div className="pt-2">
                {ROLE_ALLOWED_TABS[user.role].includes('canal') ? (
                  <button
                    onClick={() => onNavigate('canal')}
                    className="w-full py-2.5 px-4 rounded-xl text-xs font-semibold bg-primary hover:bg-indigo-700 text-white shadow-sm transition-all active:scale-95 flex items-center justify-center gap-2"
                  >
                    <ShieldCheck className="w-4 h-4" />
                    <span>Ir al Canal Seguro E2EE</span>
                  </button>
                ) : (
                  <button
                    onClick={() => onNavigate('ledger')}
                    className="w-full py-2.5 px-4 rounded-xl text-xs font-semibold bg-primary hover:bg-indigo-700 text-white shadow-sm transition-all active:scale-95 flex items-center justify-center gap-2"
                  >
                    <ShieldCheck className="w-4 h-4" />
                    <span>Ir al Registro de Ledger</span>
                  </button>
                )}
              </div>
            </div>

            {/* Quick Role Info Banner */}
            <div className="p-5 rounded-2xl bg-neutral-50 dark:bg-[#111827] border border-neutral-200 dark:border-neutral-800 space-y-2">
              <h4 className="text-xs font-bold text-neutral-800 dark:text-neutral-200 uppercase tracking-wider">
                Sobre el Rol de {user.roleLabel}
              </h4>
              <p className="text-xs text-neutral-600 dark:text-neutral-400 leading-relaxed">
                Este perfil cuenta con autorización para auditar inferencias emitidas por el modelo local Ollama, revisar la cadena inalterable de bloques SHA-256 e interactuar a través del Canal Seguro con otros custodios gubernamentales.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Ajustes del Sistema */}
      {activeTab === 'settings' && (
        <div className="max-w-3xl space-y-6 animate-fade-in">
          <div className="p-6 rounded-2xl bg-white dark:bg-[#0c121e] border border-neutral-200 dark:border-neutral-800 shadow-sm space-y-6">
            <h2 className="text-sm font-bold text-neutral-900 dark:text-white uppercase tracking-wider pb-3 border-b border-neutral-100 dark:border-neutral-800/80">
              Preferencias Visuales y de Interfaz
            </h2>

            {/* Dark Mode Toggle Item */}
            <div className="flex items-center justify-between p-4 rounded-xl bg-neutral-50 dark:bg-[#111827] border border-neutral-200/80 dark:border-neutral-800/80">
              <div className="space-y-0.5">
                <h3 className="text-xs font-bold text-neutral-900 dark:text-white flex items-center gap-2">
                  {darkMode ? <Moon className="w-4 h-4 text-indigo-400" /> : <Sun className="w-4 h-4 text-amber-500" />}
                  Tema de la Interfaz (Modo Oscuro / Claro)
                </h3>
                <p className="text-xs text-neutral-500 dark:text-neutral-400">
                  Alterna entre el modo soberano oscuro de alto contraste y el modo institucional claro.
                </p>
              </div>
              <button
                onClick={onToggleDarkMode}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-neutral-200 dark:bg-neutral-800 text-neutral-800 dark:text-neutral-200 hover:bg-neutral-300 dark:hover:bg-neutral-700 transition-colors"
              >
                {darkMode ? 'Cambiar a Modo Claro' : 'Cambiar a Modo Oscuro'}
              </button>
            </div>

            {/* PII Sanitization Toggle */}
            <div className="flex items-center justify-between p-4 rounded-xl bg-neutral-50 dark:bg-[#111827] border border-neutral-200/80 dark:border-neutral-800/80">
              <div className="space-y-0.5">
                <h3 className="text-xs font-bold text-neutral-900 dark:text-white">
                  Ofuscación Homomórfica de PII Automática
                </h3>
                <p className="text-xs text-neutral-500 dark:text-neutral-400">
                  Reemplaza cédulas, teléfonos y cuentas con tokens matemáticos antes de cualquier inferencia.
                </p>
              </div>
              <button
                onClick={() => setAutoMaskPII(!autoMaskPII)}
                className={`w-12 h-6 rounded-full transition-colors p-0.5 flex items-center ${
                  autoMaskPII ? 'bg-emerald-500 justify-end' : 'bg-slate-300 dark:bg-slate-700 justify-start'
                }`}
              >
                <span className="w-5 h-5 rounded-full bg-white shadow-xs" />
              </button>
            </div>

            {/* Notification Toggle */}
            <div className="flex items-center justify-between p-4 rounded-xl bg-neutral-50 dark:bg-[#111827] border border-neutral-200/80 dark:border-neutral-800/80">
              <div className="space-y-0.5">
                <h3 className="text-xs font-bold text-neutral-900 dark:text-white flex items-center gap-1.5">
                  <BellRing className="w-3.5 h-3.5 text-primary" />
                  Alertas de Desajuste Criptográfico en Tiempo Real
                </h3>
                <p className="text-xs text-neutral-500 dark:text-neutral-400">
                  Notificar de inmediato si ocurre una ruptura de consenso en los bloques del Ledger.
                </p>
              </div>
              <button
                onClick={() => setLedgerAuditNotify(!ledgerAuditNotify)}
                className={`w-12 h-6 rounded-full transition-colors p-0.5 flex items-center ${
                  ledgerAuditNotify ? 'bg-emerald-500 justify-end' : 'bg-slate-300 dark:bg-slate-700 justify-start'
                }`}
              >
                <span className="w-5 h-5 rounded-full bg-white shadow-xs" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Enclave Criptográfico & Llaves */}
      {activeTab === 'security' && (
        <div className="max-w-3xl space-y-6 animate-fade-in">
          <div className="p-6 rounded-2xl bg-white dark:bg-[#0c121e] border border-neutral-200 dark:border-neutral-800 shadow-sm space-y-6">
            <h2 className="text-sm font-bold text-neutral-900 dark:text-white uppercase tracking-wider pb-3 border-b border-neutral-100 dark:border-neutral-800/80">
              Gestión de Llaves y Seguridad de Enclave
            </h2>

            {rotatedKeyMessage && (
              <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-700 dark:text-emerald-300 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                <span>{rotatedKeyMessage}</span>
              </div>
            )}

            <div className="space-y-4 text-xs">
              <div className="p-4 rounded-xl bg-neutral-50 dark:bg-[#111827] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-neutral-900 dark:text-white">Llave de Sesión Ed25519 Activa:</span>
                  <span className="text-[11px] font-mono text-emerald-600 dark:text-emerald-400 font-bold">VÁLIDA</span>
                </div>
                <p className="font-mono text-neutral-600 dark:text-neutral-300 break-all p-2 bg-white dark:bg-[#0c121e] rounded-lg border border-neutral-200 dark:border-neutral-800">
                  {creds.ed25519Key}
                </p>
              </div>

              <div className="flex items-center justify-between pt-2">
                <div>
                  <h4 className="font-bold text-neutral-900 dark:text-white">Rotar Clave Efímera de Sesión</h4>
                  <p className="text-neutral-500 dark:text-neutral-400 text-[11px]">
                    Re-autentica el enclave criptográfico sin cerrar la sesión actual.
                  </p>
                </div>
                <button
                  onClick={handleRotateKey}
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800/60 hover:bg-indigo-100 transition-colors flex items-center gap-1.5"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Rotar Clave</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
