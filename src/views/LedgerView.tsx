import React, { useState } from 'react';
import { 
  ShieldCheck, 
  ShieldAlert, 
  AlertTriangle, 
  RotateCcw, 
  Copy, 
  Check, 
  CheckCircle2, 
  GraduationCap, 
  Box, 
  Key, 
  Lock, 
  RefreshCw, 
  Settings2,
  Edit3,
  Power
} from 'lucide-react';
import { EditBlockModal } from '../components/EditBlockModal';

interface LedgerViewProps {
  onCopyText: (text: string) => void;
}

export const LedgerView: React.FC<LedgerViewProps> = ({ onCopyText }) => {
  // Tampering state: default is tampered as shown in the screenshot
  const [isTampered, setIsTampered] = useState(true);
  const [isVerifying, setIsVerifying] = useState(false);
  const [copiedHash, setCopiedHash] = useState<string | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);

  // Block #004 dynamic state
  const [block4Payload, setBlock4Payload] = useState(
    'Modificación no autorizada de subvención pública [Parámetro de subsidio forzado al 100%]'
  );
  const [block4Hash, setBlock4Hash] = useState(
    '0xff4a12ec7009da331908bf293e502c334fae9102456b23d04e1c7f8934b12c34'
  );

  const pristineBlock4Hash = '0x1c3a8e9d4b2f5a6c7e8d9b0a1f2e3d4c5b6a7f8e9d0c1b2a3f4e5d6c7b8a9f0e';
  const pristineBlock4Payload = 'Ajuste regular de subvención pública [Parámetro verificado: 15% Vulnerabilidad Social]';

  const handleCopy = (hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(hash);
    onCopyText('Hash SHA-256 copiado al portapapeles');
    setTimeout(() => setCopiedHash(null), 2500);
  };

  const handleVerifyIntegrity = () => {
    setIsVerifying(true);
    setTimeout(() => {
      setIsVerifying(false);
      if (isTampered) {
        onCopyText('Auditoría completada: Desajuste detectado en Bloque #004. Cadena en aislamiento.');
      } else {
        onCopyText('Auditoría completada: 4/4 Bloques íntegros y validados con éxito.');
      }
    }, 800);
  };

  const handleRestoreOriginal = () => {
    setIsTampered(false);
    setBlock4Payload(pristineBlock4Payload);
    setBlock4Hash(pristineBlock4Hash);
    onCopyText('Bloque #004 restaurado a su estado canónico original.');
  };

  const handleSimulateTamper = () => {
    setIsTampered(!isTampered);
    if (!isTampered) {
      setBlock4Payload('Modificación no autorizada de subvención pública [Parámetro de subsidio forzado al 100%]');
      setBlock4Hash('0xff4a12ec7009da331908bf293e502c334fae9102456b23d04e1c7f8934b12c34');
      onCopyText('Simulación activada: Bloque #004 alterado intencionalmente.');
    } else {
      handleRestoreOriginal();
    }
  };

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 transition-colors">
      
      {/* 1. Header Section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-transparent">
        <div>
          {/* Eyebrow / Overline */}
          <div className="text-[11px] font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400 font-semibold flex items-center gap-1.5">
            <span>CONSORCIO GOVTECH</span>
            <span>·</span>
            <span>NODO SOBERANO #01</span>
            <span>·</span>
            <span className="text-slate-600 dark:text-slate-300 font-bold">Red Nacional de Integridad</span>
          </div>

          {/* Heading & Subtitle */}
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight mt-1">
            Registro de Auditoría Inalterable
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 mt-1 max-w-2xl font-normal leading-relaxed">
            Trazabilidad criptográfica SHA-256 de todas las inferencias y decisiones públicas del sistema aduanero.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2.5 shrink-0 self-start md:self-center">
          <button
            onClick={handleSimulateTamper}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700/60 shadow-xs transition-colors"
          >
            <Settings2 className="w-3.5 h-3.5 text-slate-500" />
            <span>{isTampered ? 'Desactivar Alteración' : 'Simular Alteración'}</span>
          </button>

          <button
            onClick={handleVerifyIntegrity}
            disabled={isVerifying}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold bg-[#3525cd] hover:bg-[#281bb5] text-white shadow-xs transition-all disabled:opacity-75"
          >
            {isVerifying ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <ShieldCheck className="w-3.5 h-3.5" />
            )}
            <span>{isVerifying ? 'Auditando...' : 'Verificar Integridad'}</span>
          </button>
        </div>
      </div>

      {/* 2. Tampering Alert Banner (Discreet & Integrated Security Notice) */}
      {isTampered && (
        <div className="mt-5 rounded-xl bg-rose-50/50 dark:bg-rose-950/20 border border-rose-200/70 dark:border-rose-900/40 p-3.5 sm:p-4 flex flex-col md:flex-row md:items-center justify-between gap-3.5 shadow-2xs transition-all">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-rose-100/80 dark:bg-rose-900/40 text-rose-600 dark:text-rose-400 border border-rose-200/60 dark:border-rose-800/40 flex items-center justify-center shrink-0 mt-0.5">
              <ShieldAlert className="w-4 h-4" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="text-xs sm:text-sm font-semibold text-slate-800 dark:text-slate-200 tracking-tight">
                  Alerta de Manipulación Detectada
                </h3>
                <span className="font-mono text-[10px] font-medium tracking-wider uppercase px-2 py-0.5 rounded bg-rose-100 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300 border border-rose-200/60 dark:border-rose-800/50">
                  DESAJUSTE SHA-256
                </span>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5 leading-relaxed">
                El Bloque #004 fue modificado externamente. La firma digital y el hash del bloque previo no coinciden con el cálculo estricto en memoria.
              </p>
            </div>
          </div>

          <button
            onClick={handleRestoreOriginal}
            className="inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-rose-700 dark:text-rose-300 bg-white dark:bg-[#1a2234] hover:bg-rose-50 dark:hover:bg-rose-950/50 border border-rose-300/80 dark:border-rose-800/60 shrink-0 shadow-2xs transition-all self-start md:self-center cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Restaurar Bloque Original</span>
          </button>
        </div>
      )}

      {/* 3. Metric Summary Cards (4 Cards) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
        
        {/* Card 1 */}
        <div className="bg-white dark:bg-[#131826] rounded-xl border border-slate-200/80 dark:border-slate-800 p-4 shadow-xs">
          <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 dark:text-slate-500 font-bold">
            PROFUNDIDAD DEL REGISTRO
          </div>
          <div className="text-xl font-extrabold text-slate-900 dark:text-white mt-1">
            4 Bloques
          </div>
          <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-700 dark:text-emerald-400 mt-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            <span>100% persistencia local</span>
          </div>
        </div>

        {/* Card 2 */}
        <div className="bg-white dark:bg-[#131826] rounded-xl border border-slate-200/80 dark:border-slate-800 p-4 shadow-xs">
          <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 dark:text-slate-500 font-bold">
            FRECUENCIA DE SELLADO
          </div>
          <div className="text-xl font-extrabold text-slate-900 dark:text-white mt-1">
            7m 35s
          </div>
          <div className="text-xs text-slate-500 dark:text-slate-400 mt-1.5 font-medium">
            Promedio por inferencia
          </div>
        </div>

        {/* Card 3 */}
        <div className="bg-white dark:bg-[#131826] rounded-xl border border-slate-200/80 dark:border-slate-800 p-4 shadow-xs">
          <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 dark:text-slate-500 font-bold">
            FIRMAS AUTORIZADAS
          </div>
          <div className="text-xl font-extrabold text-slate-900 dark:text-white mt-1">
            8/8 Custodios
          </div>
          <div className="flex items-center gap-1.5 text-xs font-semibold text-indigo-700 dark:text-indigo-400 mt-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-500" />
            <span>Quórum Gov-Ed25519</span>
          </div>
        </div>

        {/* Card 4 (Dynamic based on tampering) */}
        <div className="bg-white dark:bg-[#131826] rounded-xl border border-slate-200/80 dark:border-slate-800 p-4 shadow-xs">
          <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 dark:text-slate-500 font-bold">
            ESTADO DE CADENA
          </div>
          <div className={`text-xl font-extrabold mt-1 ${isTampered ? 'text-[#ba1a1a] dark:text-red-400' : 'text-emerald-700 dark:text-emerald-400'}`}>
            {isTampered ? 'En Aislamiento' : 'Íntegra y Verificada'}
          </div>
          <div className={`flex items-center gap-1.5 text-xs font-semibold mt-1.5 ${isTampered ? 'text-[#ba1a1a] dark:text-red-400' : 'text-emerald-700 dark:text-emerald-400'}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${isTampered ? 'bg-[#ba1a1a] animate-ping' : 'bg-emerald-500'}`} />
            <span>{isTampered ? '1 nodo en cuarentena' : 'Consenso sincronizado'}</span>
          </div>
        </div>

      </div>

      {/* 4. Vertical Blockchain Timeline & Blocks */}
      <div className="mt-8 relative">
        {/* Continuous hairline connector line */}
        <div className="absolute left-[20px] sm:left-[22px] top-6 bottom-10 w-[2px] bg-slate-200 dark:bg-slate-800 z-0" />

        <div className="space-y-6 relative z-10">
          
          {/* ================= BLOCK #001 ================= */}
          <div className="flex items-start gap-3 sm:gap-4">
            {/* Timeline Node Icon */}
            <div className="w-11 h-11 rounded-full bg-emerald-50 dark:bg-emerald-950/60 border-2 border-emerald-500 flex items-center justify-center text-emerald-600 dark:text-emerald-400 shrink-0 shadow-xs">
              <Box className="w-5 h-5" strokeWidth={1.8} />
            </div>

            {/* Block Card */}
            <div className="flex-1 bg-white dark:bg-[#131826] rounded-xl border border-slate-200/80 dark:border-slate-800 p-4 sm:p-5 shadow-xs overflow-hidden">
              
              {/* Header row */}
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                    Bloque #001
                  </h3>
                  <span className="font-mono text-[11px] text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded">
                    14:15:02 UTC
                  </span>
                  <span className="text-[11px] font-medium text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded-full">
                    Genesis
                  </span>
                </div>

                <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200/80 dark:bg-emerald-950/50 dark:text-emerald-400 dark:border-emerald-800/80">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                  <span>Verificado</span>
                </div>
              </div>

              {/* Transaction Purpose */}
              <div className="mt-3">
                <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 dark:text-slate-500 font-bold">
                  PROPÓSITO TRANSACCIONAL
                </div>
                <p className="text-xs sm:text-sm text-slate-800 dark:text-slate-200 font-medium mt-0.5">
                  Inicialización de Políticas Gov-2025 y Carga de Guardián
                </p>
              </div>

              {/* Hash Box */}
              <div className="mt-3 p-3 rounded-lg bg-slate-50 dark:bg-slate-900/70 border border-slate-200/70 dark:border-slate-800 flex items-center justify-between gap-2">
                <div className="min-w-0 font-mono text-[11px] text-slate-700 dark:text-slate-300 break-all">
                  <span className="font-semibold text-slate-400 dark:text-slate-500 mr-2">HASH ACTUAL:</span>
                  <span>0xe3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855</span>
                </div>
                <button
                  onClick={() => handleCopy('0xe3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')}
                  className="p-1.5 rounded text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-800 shrink-0 transition-colors"
                  title="Copiar Hash"
                >
                  {copiedHash === '0xe3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855' ? (
                    <Check className="w-3.5 h-3.5 text-emerald-600" />
                  ) : (
                    <Copy className="w-3.5 h-3.5" />
                  )}
                </button>
              </div>

              {/* Footer Meta */}
              <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex flex-wrap items-center gap-x-4 gap-y-1 font-mono text-[11px] text-slate-500 dark:text-slate-400">
                <span>Firma Raíz: <strong className="text-slate-700 dark:text-slate-300">ED-PUBKEY-9821</strong></span>
                <span>·</span>
                <span>Gas: <strong className="text-slate-700 dark:text-slate-300">0.00 GWEI</strong></span>
                <span>·</span>
                <span className="text-emerald-700 dark:text-emerald-400 font-semibold">Inmutable</span>
              </div>
            </div>
          </div>

          {/* ================= BLOCK #002 ================= */}
          <div className="flex items-start gap-3 sm:gap-4">
            {/* Timeline Node Icon */}
            <div className="w-11 h-11 rounded-full bg-emerald-50 dark:bg-emerald-950/60 border-2 border-emerald-500 flex items-center justify-center text-emerald-600 dark:text-emerald-400 shrink-0 shadow-xs">
              <CheckCircle2 className="w-5 h-5" strokeWidth={1.8} />
            </div>

            {/* Block Card */}
            <div className="flex-1 bg-white dark:bg-[#131826] rounded-xl border border-slate-200/80 dark:border-slate-800 p-4 sm:p-5 shadow-xs overflow-hidden">
              
              {/* Header row */}
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                    Bloque #002
                  </h3>
                  <span className="font-mono text-[11px] text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded">
                    14:22:45 UTC
                  </span>
                  <span className="text-[11px] font-medium text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded-full">
                    Aduana Express
                  </span>
                </div>

                <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200/80 dark:bg-emerald-950/50 dark:text-emerald-400 dark:border-emerald-800/80">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                  <span>Verificado</span>
                </div>
              </div>

              {/* Transaction Purpose */}
              <div className="mt-3">
                <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 dark:text-slate-500 font-bold">
                  PROPÓSITO TRANSACCIONAL
                </div>
                <p className="text-xs sm:text-sm text-slate-800 dark:text-slate-200 font-medium mt-0.5">
                  Trámite Solvencia Fiscal • Cédula [V-XX.XXX.XXX] sanitizada con cifrado homomórfico
                </p>
              </div>

              {/* Hash Box */}
              <div className="mt-3 p-3 rounded-lg bg-slate-50 dark:bg-slate-900/70 border border-slate-200/70 dark:border-slate-800 flex items-center justify-between gap-2">
                <div className="min-w-0 font-mono text-[11px] text-slate-700 dark:text-slate-300 break-all">
                  <span className="font-semibold text-slate-400 dark:text-slate-500 mr-2">HASH ACTUAL:</span>
                  <span>0x7d2f9a1b8c0e5d4a3f2b1a0e9d8c7b6a5f4e3d2c1b0a9f8e7d6c5b4a3f2e1d0c</span>
                </div>
                <button
                  onClick={() => handleCopy('0x7d2f9a1b8c0e5d4a3f2b1a0e9d8c7b6a5f4e3d2c1b0a9f8e7d6c5b4a3f2e1d0c')}
                  className="p-1.5 rounded text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-800 shrink-0 transition-colors"
                  title="Copiar Hash"
                >
                  {copiedHash === '0x7d2f9a1b8c0e5d4a3f2b1a0e9d8c7b6a5f4e3d2c1b0a9f8e7d6c5b4a3f2e1d0c' ? (
                    <Check className="w-3.5 h-3.5 text-emerald-600" />
                  ) : (
                    <Copy className="w-3.5 h-3.5" />
                  )}
                </button>
              </div>

              {/* Footer Meta */}
              <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex flex-wrap items-center gap-x-4 gap-y-1 font-mono text-[11px] text-slate-500 dark:text-slate-400">
                <span>Hash Previo: <strong className="text-slate-700 dark:text-slate-300">0xe3b0c442...</strong></span>
                <span>·</span>
                <span>Declaración Aduanera: <strong className="text-slate-700 dark:text-slate-300">DGC-89211</strong></span>
              </div>
            </div>
          </div>

          {/* ================= BLOCK #003 ================= */}
          <div className="flex items-start gap-3 sm:gap-4">
            {/* Timeline Node Icon */}
            <div className="w-11 h-11 rounded-full bg-emerald-50 dark:bg-emerald-950/60 border-2 border-emerald-500 flex items-center justify-center text-emerald-600 dark:text-emerald-400 shrink-0 shadow-xs">
              <GraduationCap className="w-5 h-5" strokeWidth={1.8} />
            </div>

            {/* Block Card */}
            <div className="flex-1 bg-white dark:bg-[#131826] rounded-xl border border-slate-200/80 dark:border-slate-800 p-4 sm:p-5 shadow-xs overflow-hidden">
              
              {/* Header row */}
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                    Bloque #003
                  </h3>
                  <span className="font-mono text-[11px] text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded">
                    14:30:19 UTC
                  </span>
                  <span className="text-[11px] font-medium text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded-full">
                    Programa Social
                  </span>
                </div>

                <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200/80 dark:bg-emerald-950/50 dark:text-emerald-400 dark:border-emerald-800/80">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                  <span>Verificado</span>
                </div>
              </div>

              {/* Transaction Purpose */}
              <div className="mt-3">
                <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 dark:text-slate-500 font-bold">
                  PROPÓSITO TRANSACCIONAL
                </div>
                <p className="text-xs sm:text-sm text-slate-800 dark:text-slate-200 font-medium mt-0.5">
                  Evaluación de Beca Estudiantil #894 • Dictamen Favorable Aprobado sin observaciones
                </p>
              </div>

              {/* Hash Box */}
              <div className="mt-3 p-3 rounded-lg bg-slate-50 dark:bg-slate-900/70 border border-slate-200/70 dark:border-slate-800 flex items-center justify-between gap-2">
                <div className="min-w-0 font-mono text-[11px] text-slate-700 dark:text-slate-300 break-all">
                  <span className="font-semibold text-slate-400 dark:text-slate-500 mr-2">HASH ACTUAL:</span>
                  <span>0x9b8a7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b</span>
                </div>
                <button
                  onClick={() => handleCopy('0x9b8a7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b')}
                  className="p-1.5 rounded text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-800 shrink-0 transition-colors"
                  title="Copiar Hash"
                >
                  {copiedHash === '0x9b8a7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b' ? (
                    <Check className="w-3.5 h-3.5 text-emerald-600" />
                  ) : (
                    <Copy className="w-3.5 h-3.5" />
                  )}
                </button>
              </div>

              {/* Footer Meta */}
              <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex flex-wrap items-center gap-x-4 gap-y-1 font-mono text-[11px] text-slate-500 dark:text-slate-400">
                <span>Hash Previo: <strong className="text-slate-700 dark:text-slate-300">0x7d2f9a1b...</strong></span>
                <span>·</span>
                <span>Puntaje Mérito: <strong className="text-slate-700 dark:text-slate-300">98.4 / 100</strong></span>
              </div>
            </div>
          </div>

          {/* ================= BLOCK #004 (Corrupted or Pristine) ================= */}
          <div className="flex items-start gap-3 sm:gap-4">
            {/* Timeline Node Icon */}
            <div className={`w-11 h-11 rounded-full border-2 flex items-center justify-center shrink-0 shadow-xs ${
              isTampered 
                ? 'bg-red-50 dark:bg-red-950/60 border-red-500 text-red-600 dark:text-red-400' 
                : 'bg-emerald-50 dark:bg-emerald-950/60 border-emerald-500 text-emerald-600 dark:text-emerald-400'
            }`}>
              {isTampered ? <Power className="w-5 h-5" strokeWidth={1.8} /> : <CheckCircle2 className="w-5 h-5" strokeWidth={1.8} />}
            </div>

            {/* Block Card */}
            <div className={`flex-1 rounded-xl border p-4 sm:p-5 shadow-xs overflow-hidden transition-all ${
              isTampered 
                ? 'bg-white dark:bg-[#131826] border-red-200 dark:border-red-900/60' 
                : 'bg-white dark:bg-[#131826] border-slate-200/80 dark:border-slate-800'
            }`}>
              
              {/* Header row */}
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                    Bloque #004
                  </h3>
                  <span className="font-mono text-[11px] text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded">
                    14:38:12 UTC
                  </span>
                  <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${
                    isTampered 
                      ? 'bg-red-50 text-red-700 dark:bg-red-950/60 dark:text-red-300 border border-red-200/60 dark:border-red-900/40' 
                      : 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
                  }`}>
                    {isTampered ? 'Alerta de Seguridad' : 'Programa Social Subvención'}
                  </span>
                </div>

                <div className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                  isTampered 
                    ? 'bg-red-100/90 text-red-800 border border-red-300 dark:bg-red-900/60 dark:text-red-200 dark:border-red-800' 
                    : 'bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/50 dark:text-emerald-400'
                }`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${isTampered ? 'bg-red-600 animate-pulse' : 'bg-emerald-500'}`} />
                  <span>{isTampered ? 'Corrupto / Alterado' : 'Verificado'}</span>
                </div>
              </div>

              {/* Transaction Purpose */}
              <div className="mt-3">
                <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 dark:text-slate-500 font-bold">
                  PROPÓSITO TRANSACCIONAL
                </div>
                <p className="text-xs sm:text-sm text-slate-800 dark:text-slate-200 font-medium mt-0.5">
                  {block4Payload}
                </p>
              </div>

              {/* Broken Consensus Box or Clean Hash Box */}
              {isTampered ? (
                <div className="mt-3 p-3.5 sm:p-4 rounded-lg bg-[#fff8f7] dark:bg-red-950/20 border border-red-200/90 dark:border-red-900/80">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 pb-2 border-b border-red-100 dark:border-red-900/60">
                    <span className="font-mono text-[10px] tracking-wider font-extrabold text-[#ba1a1a] dark:text-red-400 uppercase flex items-center gap-1.5">
                      <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                      RUPTURA DE CONSENSO CRIPTOGRÁFICO
                    </span>
                    <span className="font-mono text-[11px] text-slate-500 dark:text-slate-400">
                      Discrepancia detectada en memoria
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-2.5">
                    <div>
                      <div className="text-[10px] font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400 font-bold">
                        HASH PREVIO ESPERADO:
                      </div>
                      <div className="font-mono text-xs text-emerald-700 dark:text-emerald-400 font-semibold break-all mt-0.5">
                        0x9b8a7c6d5e4f3a2b1c0d9e...
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400 font-bold">
                        HASH CALCULADO CORRUPTO:
                      </div>
                      <div className="font-mono text-xs text-red-600 dark:text-red-400 font-bold break-all mt-0.5">
                        {block4Hash.slice(0, 26)}...
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="mt-3 p-3 rounded-lg bg-slate-50 dark:bg-slate-900/70 border border-slate-200/70 dark:border-slate-800 flex items-center justify-between gap-2">
                  <div className="min-w-0 font-mono text-[11px] text-slate-700 dark:text-slate-300 break-all">
                    <span className="font-semibold text-slate-400 dark:text-slate-500 mr-2">HASH ACTUAL:</span>
                    <span>{block4Hash}</span>
                  </div>
                  <button
                    onClick={() => handleCopy(block4Hash)}
                    className="p-1.5 rounded text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-800 shrink-0 transition-colors"
                  >
                    <Copy className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}

              {/* Footer Meta & Edit Button */}
              <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex flex-wrap items-center justify-between gap-2">
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1 font-mono text-[11px]">
                  <span className={isTampered ? 'text-red-600 dark:text-red-400 font-bold' : 'text-emerald-600 font-bold'}>
                    Firma: {isTampered ? 'INVÁLIDA' : 'VÁLIDA (Ed25519)'}
                  </span>
                  <span className="text-slate-400">·</span>
                  <span className="text-slate-600 dark:text-slate-400">
                    Vector de Ataque: <strong className="text-slate-700 dark:text-slate-300">{isTampered ? 'Sobrescritura Directa de DB' : 'Ninguno (Íntegro)'}</strong>
                  </span>
                </div>

                <button
                  onClick={() => setIsEditModalOpen(true)}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700 shadow-xs transition-colors"
                >
                  <Edit3 className="w-3.5 h-3.5 text-slate-500" />
                  <span>Editar para probar</span>
                </button>
              </div>

            </div>
          </div>

        </div>
      </div>

      {/* 5. Bottom Status Bar & Indicators */}
      <div className="mt-8 bg-white dark:bg-[#131826] rounded-xl border border-slate-200/80 dark:border-slate-800 p-4 shadow-xs">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          
          {/* Status Pills */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-medium bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
              <Key className="w-3 h-3 text-[#3525cd] dark:text-indigo-400" />
              <span>Consenso: Ed25519 Institucional</span>
            </span>

            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-medium bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
              <Lock className="w-3 h-3 text-indigo-600 dark:text-indigo-400" />
              <span>Algoritmo: SHA-256 Gov-Hardened</span>
            </span>

            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-medium bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
              <Check className="w-3 h-3 text-emerald-600" />
              <span>Bloques Válidos: {isTampered ? '3/4' : '4/4'}</span>
            </span>

            <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-bold border ${
              isTampered 
                ? 'bg-red-50 text-[#ba1a1a] border-red-200 dark:bg-red-950/40 dark:text-red-400 dark:border-red-900/60' 
                : 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-900/60'
            }`}>
              <span className={`w-1.5 h-1.5 rounded-full ${isTampered ? 'bg-red-500 animate-ping' : 'bg-emerald-500'}`} />
              <span>Estado: {isTampered ? 'En Aislamiento Preventivo' : 'Cadena Íntegra y Operativa'}</span>
            </span>
          </div>

          {/* Sync Metadata */}
          <div className="flex items-center gap-3 font-mono text-[11px] text-slate-500 dark:text-slate-400 shrink-0">
            <span>Último sync: <strong>Hace 12 seg</strong></span>
            <span>·</span>
            <span className="text-emerald-700 dark:text-emerald-400 font-semibold">Red: Sincronizada</span>
          </div>

        </div>
      </div>

      {/* Edit Block Modal */}
      <EditBlockModal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        initialPayload={block4Payload}
        onSaveTampered={(newPayload, newHash) => {
          setBlock4Payload(newPayload);
          setBlock4Hash(newHash);
          setIsTampered(true);
          onCopyText('Modificación inyectada en Bloque #004. Consenso roto.');
        }}
        onRestore={handleRestoreOriginal}
      />
    </div>
  );
};
