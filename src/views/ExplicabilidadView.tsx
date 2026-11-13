import React, { useState } from 'react';
import { 
  ShieldCheck, 
  Download, 
  Scale, 
  CheckCircle2, 
  Copy, 
  Check, 
  User, 
  Bot, 
  Building2
} from 'lucide-react';
import { ProofModal } from '../components/ProofModal';

interface ExplicabilidadViewProps {
  onNotify: (msg: string) => void;
}

export const ExplicabilidadView: React.FC<ExplicabilidadViewProps> = ({ onNotify }) => {
  const [copiedHash, setCopiedHash] = useState<string | null>(null);
  const [isProofModalOpen, setIsProofModalOpen] = useState(false);
  const [selectedFactor, setSelectedFactor] = useState<number | null>(null);

  const sha256VerificationHash = 'd8f4a13e2698cbb378214ef39e0811ca34fd018bc9e022';

  const handleCopy = (hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(hash);
    onNotify('Hash criptográfico copiado al portapapeles');
    setTimeout(() => setCopiedHash(null), 2500);
  };

  const handleDownloadDictamen = () => {
    const dictamenData = {
      titulo: 'Dictamen Oficial de Explicabilidad Algorítmica',
      expediente: 'Evaluación de Beca Estudiantil #894',
      postulante: 'Camila Rivas',
      carrera: 'Ingeniería en Telecomunicaciones',
      puntaje_final: 78,
      umbral_minimo: 65,
      dictamen_ia: 'Aprobada (94.6% de confianza)',
      criterio_funcionario: 'Aprobada (Auditor L. Santander - DGA-08)',
      concordancia: '100% Homogénea',
      factores_shap: [
        { variable: 'Promedio Académico (9.4 / 10)', peso: '+34% Impacto Positivo', percentil: 'Superior Nacional' },
        { variable: 'Situación Socioeconómica (Estrato B)', peso: '+28% Prioridad Social', validado: 'Cruce Tesoro' },
        { variable: 'Distancia y Desplazamiento (42 km)', peso: '+16% Movilidad', trayecto: '> 90 min' },
        { variable: 'Voluntariado Comunitario', peso: '+8% Mérito Cívico', horas: 120 },
        { variable: 'Carga Prestacional Previa', peso: '-8% Factor Ponderado', deduccion: 'Subsidio transporte activo' }
      ],
      verificacion_sha256: sha256VerificationHash,
      modelo_auditor: 'GovEval-XGBoost v4.2',
      paridad_impacto: '0.98 / 1.00 (Sin sesgo demográfico)',
      fecha_emision: new Date().toISOString(),
      sello_soberano: 'Consorcio GovTech · Nodo Soberano #01'
    };

    const blob = new Blob([JSON.stringify(dictamenData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'Dictamen-Beca-894-Soberano.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    onNotify('Dictamen oficial descargado en formato JSON auditable.');
  };

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 transition-colors">
      
      {/* 1. Header Section */}
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
        <div>
          {/* Top Badges */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full text-[11px] font-mono font-semibold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-500" />
              <span>SUPERVISIÓN ALGORÍTMICA PÚBLICA</span>
            </span>

            <span className="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full text-[11px] font-mono font-semibold bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-400 border border-emerald-200/80 dark:border-emerald-800/80">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
              <span>Norma ENISA Gov-AI · Nivel A+</span>
            </span>
          </div>

          {/* Heading & Subtitle */}
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight mt-2.5">
            Explicabilidad & Equidad Decisional
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 mt-1 max-w-2xl font-normal leading-relaxed">
            Trazabilidad comprensible de decisiones automatizadas del sector público bajo el marco de soberanía y auditoría algorítmica.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2.5 shrink-0 self-start md:self-center">
          <button
            onClick={handleDownloadDictamen}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700/60 shadow-xs transition-colors"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" />
            <span>Descargar Dictamen</span>
          </button>

          <button
            onClick={() => setIsProofModalOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold bg-[#3525cd] hover:bg-[#281bb5] text-white shadow-xs transition-all"
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Firma Criptográfica</span>
          </button>
        </div>
      </div>

      {/* 2. Main Case Header Card (Expediente) */}
      <div className="mt-6 bg-white dark:bg-[#131826] rounded-2xl border border-slate-200/80 dark:border-slate-800 p-5 sm:p-6 shadow-xs transition-colors">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-5">
          
          {/* Left Details */}
          <div>
            <div className="text-[11px] font-mono uppercase tracking-wider text-[#3525cd] dark:text-indigo-400 font-bold">
              EXPEDIENTE OFICIAL — Beca Universitaria Excelencia
            </div>
            <h2 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white tracking-tight mt-1">
              Evaluación de Beca Estudiantil #894
            </h2>
            <div className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1 flex flex-wrap items-center gap-x-2 gap-y-1">
              <span className="font-semibold text-slate-700 dark:text-slate-200">Camila Rivas</span>
              <span>•</span>
              <span className="font-mono text-xs">Expediente Académico 2025-8E</span>
              <span>•</span>
              <span>Carrera: Ingeniería en Telecomunicaciones</span>
            </div>
          </div>

          {/* Right Circular Gauge */}
          <div className="flex items-center gap-4 shrink-0 sm:border-l sm:border-slate-200 dark:sm:border-slate-800 sm:pl-6">
            {/* SVG Donut Circle */}
            <div className="relative w-16 h-16 flex items-center justify-center">
              <svg className="w-16 h-16 transform -rotate-90" viewBox="0 0 36 36">
                {/* Background Ring */}
                <path
                  className="text-slate-100 dark:text-slate-800"
                  strokeWidth="3.2"
                  stroke="currentColor"
                  fill="none"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
                {/* Progress Ring (78%) */}
                <path
                  className="text-[#006c49] dark:text-emerald-500 transition-all duration-1000 ease-out"
                  strokeDasharray="78, 100"
                  strokeWidth="3.2"
                  strokeLinecap="round"
                  stroke="currentColor"
                  fill="none"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                <span className="font-mono text-sm font-extrabold text-slate-900 dark:text-white leading-none">
                  78
                </span>
                <span className="text-[8px] font-mono text-slate-400 leading-none mt-0.5">
                  / 100
                </span>
              </div>
            </div>

            {/* Gauge Label & Status */}
            <div>
              <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-400 border border-emerald-200/80 dark:border-emerald-800/80">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                <span>Aprobada por Unanimidad</span>
              </div>
              <div className="font-mono text-[11px] text-slate-500 dark:text-slate-400 mt-1">
                Umbral Mínimo: <strong>65 pts</strong>
              </div>
            </div>

          </div>

        </div>
      </div>

      {/* 3. Tri-Panel Decision Concordance (3 Cards Row) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
        
        {/* Card 1 */}
        <div className="bg-white dark:bg-[#131826] rounded-xl border border-slate-200/80 dark:border-slate-800 p-4 shadow-xs">
          <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 dark:text-slate-500 font-bold">
            DICTAMEN IA PREDICTIVA
          </div>
          <div className="text-base font-bold text-slate-900 dark:text-white mt-1 flex items-center gap-2">
            <div className="p-1 rounded-md bg-indigo-50 dark:bg-indigo-950/60 text-[#3525cd] dark:text-indigo-400">
              <Bot className="w-4 h-4" />
            </div>
            <span>Aprobada</span>
          </div>
          <div className="font-mono text-xs text-slate-500 dark:text-slate-400 mt-1.5">
            Confianza del modelo: <strong className="text-slate-700 dark:text-slate-300">94.6%</strong>
          </div>
        </div>

        {/* Card 2 */}
        <div className="bg-white dark:bg-[#131826] rounded-xl border border-slate-200/80 dark:border-slate-800 p-4 shadow-xs">
          <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 dark:text-slate-500 font-bold">
            CRITERIO FUNCIONARIO HUMANO
          </div>
          <div className="text-base font-bold text-slate-900 dark:text-white mt-1 flex items-center gap-2">
            <div className="p-1 rounded-md bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400">
              <User className="w-4 h-4" />
            </div>
            <span>Aprobada</span>
          </div>
          <div className="font-mono text-xs text-slate-500 dark:text-slate-400 mt-1.5">
            Auditor: <strong className="text-slate-700 dark:text-slate-300">L. Santander (DGA-08)</strong>
          </div>
        </div>

        {/* Card 3 */}
        <div className="bg-white dark:bg-[#131826] rounded-xl border border-slate-200/80 dark:border-slate-800 p-4 shadow-xs">
          <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 dark:text-slate-500 font-bold">
            CONCORDANCIA INSTITUCIONAL
          </div>
          <div className="text-base font-bold text-emerald-700 dark:text-emerald-400 mt-1 flex items-center gap-2">
            <div className="p-1 rounded-md bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <span>100% Homogénea</span>
          </div>
          <div className="text-xs text-slate-500 dark:text-slate-400 mt-1.5 font-medium">
            Cero discrepancia regulatoria
          </div>
        </div>

      </div>

      {/* 4. Core Body: Two-Column Layout (7 cols / 5 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mt-6 items-start">
        
        {/* ================= LEFT COLUMN: SHAP FACTOR BREAKDOWN (7 Cols) ================= */}
        <div className="lg:col-span-7 bg-white dark:bg-[#131826] rounded-2xl border border-slate-200/80 dark:border-slate-800 p-5 sm:p-6 shadow-xs">
          
          <div className="text-[10px] font-mono uppercase tracking-wider text-[#3525cd] dark:text-indigo-400 font-bold">
            DESGLOSE DE FACTORES RELEVANTES
          </div>
          <h3 className="text-lg font-bold text-slate-900 dark:text-white tracking-tight mt-1">
            ¿Por qué la IA tomó esta decisión?
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 mb-6 leading-relaxed">
            Ponderación de variables según el marco oficial de evaluación pública:
          </p>

          {/* Factor Items List */}
          <div className="space-y-5">
            
            {/* Factor 1 */}
            <div 
              onClick={() => setSelectedFactor(selectedFactor === 1 ? null : 1)}
              className="cursor-pointer group p-2 -mx-2 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors"
            >
              <div className="flex items-center justify-between gap-2 text-xs">
                <span className="font-semibold text-slate-800 dark:text-slate-200 group-hover:text-[#3525cd] dark:group-hover:text-indigo-400 transition-colors">
                  Promedio Académico (9.4 / 10)
                </span>
                <span className="font-mono text-xs font-bold text-[#006c49] dark:text-emerald-400">
                  +34% Impacto Positivo
                </span>
              </div>
              <div className="w-full h-2 rounded-full bg-slate-100 dark:bg-slate-800 mt-2 overflow-hidden">
                <div className="h-full rounded-full bg-[#006c49] dark:bg-emerald-500" style={{ width: '82%' }} />
              </div>
              <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-1.5 font-normal">
                Percentil superior nacional en su cohorte universitaria
              </div>
              {selectedFactor === 1 && (
                <div className="mt-2 p-2 rounded-lg bg-indigo-50/60 dark:bg-indigo-950/40 text-[11px] font-mono text-slate-600 dark:text-slate-300 border border-indigo-100 dark:border-indigo-900/60">
                  SHAP lineal: φ₁ = β₁ · (9.4 - μ₁) = +1.48 logit · Contribución decisoria dominante
                </div>
              )}
            </div>

            {/* Factor 2 */}
            <div 
              onClick={() => setSelectedFactor(selectedFactor === 2 ? null : 2)}
              className="cursor-pointer group p-2 -mx-2 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors"
            >
              <div className="flex items-center justify-between gap-2 text-xs">
                <span className="font-semibold text-slate-800 dark:text-slate-200 group-hover:text-[#3525cd] dark:group-hover:text-indigo-400 transition-colors">
                  Situación Socioeconómica Vulnerable (Estrato B)
                </span>
                <span className="font-mono text-xs font-bold text-[#006c49] dark:text-emerald-400">
                  +28% Prioridad Social
                </span>
              </div>
              <div className="w-full h-2 rounded-full bg-slate-100 dark:bg-slate-800 mt-2 overflow-hidden">
                <div className="h-full rounded-full bg-[#006c49] dark:bg-emerald-500" style={{ width: '68%' }} />
              </div>
              <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-1.5 font-normal">
                Verificación de ingresos per cápita cruzada con bases del Tesoro
              </div>
              {selectedFactor === 2 && (
                <div className="mt-2 p-2 rounded-lg bg-indigo-50/60 dark:bg-indigo-950/40 text-[11px] font-mono text-slate-600 dark:text-slate-300 border border-indigo-100 dark:border-indigo-900/60">
                  SHAP lineal: φ₂ = β₂ · (Estrato_B - μ₂) = +1.12 logit · Validación vía blind_citizen_id
                </div>
              )}
            </div>

            {/* Factor 3 */}
            <div 
              onClick={() => setSelectedFactor(selectedFactor === 3 ? null : 3)}
              className="cursor-pointer group p-2 -mx-2 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors"
            >
              <div className="flex items-center justify-between gap-2 text-xs">
                <span className="font-semibold text-slate-800 dark:text-slate-200 group-hover:text-[#3525cd] dark:group-hover:text-indigo-400 transition-colors">
                  Distancia y Desplazamiento Domiciliario (42 km)
                </span>
                <span className="font-mono text-xs font-bold text-teal-700 dark:text-teal-400">
                  +16% Movilidad
                </span>
              </div>
              <div className="w-full h-2 rounded-full bg-slate-100 dark:bg-slate-800 mt-2 overflow-hidden">
                <div className="h-full rounded-full bg-teal-600 dark:bg-teal-500" style={{ width: '42%' }} />
              </div>
              <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-1.5 font-normal">
                Tiempo estimado de trayecto interurbano mayor a 90 minutos
              </div>
            </div>

            {/* Factor 4 */}
            <div 
              onClick={() => setSelectedFactor(selectedFactor === 4 ? null : 4)}
              className="cursor-pointer group p-2 -mx-2 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors"
            >
              <div className="flex items-center justify-between gap-2 text-xs">
                <span className="font-semibold text-slate-800 dark:text-slate-200 group-hover:text-[#3525cd] dark:group-hover:text-indigo-400 transition-colors">
                  Actividades de Voluntariado Comunitario
                </span>
                <span className="font-mono text-xs font-bold text-cyan-700 dark:text-cyan-400">
                  +8% Mérito Cívico
                </span>
              </div>
              <div className="w-full h-2 rounded-full bg-slate-100 dark:bg-slate-800 mt-2 overflow-hidden">
                <div className="h-full rounded-full bg-cyan-600 dark:bg-cyan-500" style={{ width: '22%' }} />
              </div>
              <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-1.5 font-normal">
                120 horas acreditadas en alfabetización digital comunitaria
              </div>
            </div>

            {/* Factor 5 (Negative Impact) */}
            <div 
              onClick={() => setSelectedFactor(selectedFactor === 5 ? null : 5)}
              className="cursor-pointer group p-2 -mx-2 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors"
            >
              <div className="flex items-center justify-between gap-2 text-xs">
                <span className="font-semibold text-slate-800 dark:text-slate-200 group-hover:text-[#3525cd] dark:group-hover:text-indigo-400 transition-colors">
                  Carga Prestacional Previa
                </span>
                <span className="font-mono text-xs font-bold text-amber-700 dark:text-amber-400">
                  -8% Factor Ponderado
                </span>
              </div>
              <div className="w-full h-2 rounded-full bg-slate-100 dark:bg-slate-800 mt-2 overflow-hidden">
                <div className="h-full rounded-full bg-amber-500 dark:bg-amber-400" style={{ width: '16%' }} />
              </div>
              <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-1.5 font-normal">
                Descuento estándar por subsidio complementario de transporte activo
              </div>
            </div>

          </div>

          {/* Peritaje Callout Box */}
          <div className="mt-6 p-4 rounded-xl bg-[#f4f2fd] dark:bg-indigo-950/30 border border-indigo-100 dark:border-indigo-900/60 flex items-start gap-3">
            <div className="p-1.5 rounded-lg bg-[#3525cd]/10 text-[#3525cd] dark:text-indigo-400 shrink-0 mt-0.5">
              <Scale className="w-4 h-4" />
            </div>
            <p className="text-xs text-indigo-950 dark:text-indigo-200 font-medium leading-relaxed">
              <strong>Conclusión Pericial:</strong> El alto rendimiento académico y la condición de vulnerabilidad socioeconómica superan con creces el umbral mínimo institucional de 65 puntos.
            </p>
          </div>

        </div>

        {/* ================= RIGHT COLUMN: PHOTO & TECHNICAL CARDS (5 Cols) ================= */}
        <div className="lg:col-span-5 space-y-4">
          
          {/* Card 1: Faculty / Lab Photo Card */}
          <div className="bg-white dark:bg-[#131826] rounded-2xl border border-slate-200/80 dark:border-slate-800 overflow-hidden shadow-xs">
            {/* Visual Engineering Lab Art / Photo Header */}
            <div className="relative h-44 sm:h-48 w-full bg-gradient-to-tr from-slate-900 via-indigo-950 to-slate-800 overflow-hidden flex items-center justify-center">
              {/* Geometric Grid Overlay */}
              <div className="absolute inset-0 bg-[radial-gradient(#4f46e5_1px,transparent_1px)] [background-size:16px_16px] opacity-25" />
              
              {/* Graphic Lab Representation */}
              <div className="relative z-10 flex flex-col items-center text-center p-4">
                <div className="w-14 h-14 rounded-2xl bg-white/10 backdrop-blur-md border border-white/20 flex items-center justify-center text-white shadow-lg mb-2">
                  <Building2 className="w-7 h-7 text-indigo-300" />
                </div>
                <div className="text-white font-bold text-sm tracking-tight drop-shadow-xs">
                  Laboratorio de Computación y Telecomunicaciones
                </div>
                <div className="text-indigo-200 text-xs font-mono mt-0.5 opacity-90">
                  Campus Universitario · Proyecto de Excelencia 2025
                </div>
              </div>

              {/* Verified Badge overlay */}
              <div className="absolute top-3 right-3 px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-emerald-500/90 text-white backdrop-blur-xs flex items-center gap-1 shadow-xs">
                <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
                <span>SEDE VALIDADA</span>
              </div>
            </div>

            {/* Photo Card Footer */}
            <div className="px-4 py-3 bg-white dark:bg-[#131826] flex items-center justify-between text-xs border-t border-slate-100 dark:border-slate-800">
              <span className="font-semibold text-slate-800 dark:text-slate-200">
                Facultad de Ingeniería — Sede Central
              </span>
              <span className="font-mono text-xs font-bold text-slate-500 dark:text-slate-400">
                ID 2025-BE
              </span>
            </div>
          </div>

          {/* Card 2: Cryptographic Verification Card */}
          <div className="bg-white dark:bg-[#131826] rounded-2xl border border-slate-200/80 dark:border-slate-800 p-4 sm:p-5 shadow-xs">
            <div className="flex items-center justify-between gap-2">
              <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 dark:text-slate-500 font-bold">
                VERIFICACIÓN CRIPTOGRÁFICA
              </div>
              <span className="font-mono text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400 border border-emerald-200/60 dark:border-emerald-800/60">
                Cadena Íntegra
              </span>
            </div>

            <div className="mt-2.5 p-2.5 rounded-lg bg-slate-50 dark:bg-slate-900/80 border border-slate-200/70 dark:border-slate-800 flex items-center justify-between gap-2">
              <div className="font-mono text-[11px] text-slate-700 dark:text-slate-300 break-all select-all">
                <span className="font-bold text-slate-400 mr-1.5">SHA256:</span>
                <span>{sha256VerificationHash}</span>
              </div>
              <button
                onClick={() => handleCopy(sha256VerificationHash)}
                className="p-1 rounded text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-800 shrink-0 transition-colors"
                title="Copiar Hash"
              >
                {copiedHash === sha256VerificationHash ? (
                  <Check className="w-3.5 h-3.5 text-emerald-600" />
                ) : (
                  <Copy className="w-3.5 h-3.5" />
                )}
              </button>
            </div>

            <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-2.5 leading-relaxed font-normal">
              Toda inferencia algorítmica queda sellada en el libro inmutable de gobernanza institucional para auditorías ciudadanas retroactivas.
            </p>
          </div>

          {/* Card 3: Ficha Técnica de Inferencia Card */}
          <div className="bg-white dark:bg-[#131826] rounded-2xl border border-slate-200/80 dark:border-slate-800 p-4 sm:p-5 shadow-xs">
            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 dark:text-slate-500 font-bold mb-3">
              FICHA TÉCNICA DE INFERENCIA
            </div>

            <div className="space-y-2.5 text-xs font-mono">
              <div className="flex items-center justify-between pb-1.5 border-b border-slate-100 dark:border-slate-800/80">
                <span className="text-slate-500 dark:text-slate-400">Modelo Auditor</span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">GovEval-XGBoost v4.2</span>
              </div>

              <div className="flex items-center justify-between pb-1.5 border-b border-slate-100 dark:border-slate-800/80">
                <span className="text-slate-500 dark:text-slate-400">Técnica de Explicabilidad</span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">SHAP Trees (Valores Shapley)</span>
              </div>

              <div className="flex items-center justify-between pb-1.5 border-b border-slate-100 dark:border-slate-800/80">
                <span className="text-slate-500 dark:text-slate-400">Latencia de Inferencia</span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">41 ms</span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-slate-500 dark:text-slate-400">Última Recalibración</span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">14 Feb 2025</span>
              </div>
            </div>
          </div>

        </div>

      </div>

      {/* 5. Bottom Card: Monitor de Equidad y Cero Sesgo Algorítmico */}
      <div className="mt-8 bg-white dark:bg-[#131826] rounded-2xl border border-slate-200/80 dark:border-slate-800 p-5 sm:p-6 shadow-xs transition-colors">
        
        {/* Top Header Row */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-100 dark:border-slate-800">
          <div>
            <div className="text-[10px] font-mono uppercase tracking-wider text-emerald-700 dark:text-emerald-400 font-bold flex items-center gap-1.5">
              <Scale className="w-3.5 h-3.5" />
              <span>GARANTÍA CONSTITUCIONAL</span>
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white tracking-tight mt-1">
              Monitor de Equidad y Cero Sesgo Algorítmico
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 leading-relaxed">
              Evaluación demográfica continua para descartar sesgos socio-espaciales o demográficos adversos.
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0 self-start md:self-center">
            <div className="text-right">
              <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold">
                DISPARIDAD DE IMPACTO
              </div>
              <div className="text-xl font-extrabold font-mono text-slate-900 dark:text-white mt-0.5">
                0.98 / 1.00
              </div>
            </div>

            <div className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-400 border border-emerald-200/80 dark:border-emerald-800/80">
              Sin Sesgo Detectado
            </div>
          </div>
        </div>

        {/* 4 Regional Metrics Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-5">
          
          {/* Region Central */}
          <div className="bg-slate-50/70 dark:bg-slate-900/60 rounded-xl border border-slate-200/60 dark:border-slate-800/80 p-4">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-800 dark:text-slate-200">Región Central</span>
              <span className="font-mono text-xs font-bold text-[#006c49] dark:text-emerald-400">99.1% Paridad</span>
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-extrabold font-mono text-slate-900 dark:text-white">76%</span>
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Tasa Aprobación</span>
            </div>
            <div className="w-full h-1.5 rounded-full bg-slate-200 dark:bg-slate-700 mt-2 overflow-hidden">
              <div className="h-full bg-slate-900 dark:bg-slate-300 rounded-full" style={{ width: '76%' }} />
            </div>
            <div className="text-[10px] font-mono text-slate-500 dark:text-slate-400 mt-2">
              Muestra auditada: <strong>4,120 solicitudes</strong>
            </div>
          </div>

          {/* Region Occidental */}
          <div className="bg-slate-50/70 dark:bg-slate-900/60 rounded-xl border border-slate-200/60 dark:border-slate-800/80 p-4">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-800 dark:text-slate-200">Región Occidental</span>
              <span className="font-mono text-xs font-bold text-[#006c49] dark:text-emerald-400">98.8% Paridad</span>
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-extrabold font-mono text-slate-900 dark:text-white">74%</span>
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Tasa Aprobación</span>
            </div>
            <div className="w-full h-1.5 rounded-full bg-slate-200 dark:bg-slate-700 mt-2 overflow-hidden">
              <div className="h-full bg-slate-900 dark:bg-slate-300 rounded-full" style={{ width: '74%' }} />
            </div>
            <div className="text-[10px] font-mono text-slate-500 dark:text-slate-400 mt-2">
              Muestra auditada: <strong>3,450 solicitudes</strong>
            </div>
          </div>

          {/* Region Oriental */}
          <div className="bg-slate-50/70 dark:bg-slate-900/60 rounded-xl border border-slate-200/60 dark:border-slate-800/80 p-4">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-800 dark:text-slate-200">Región Oriental</span>
              <span className="font-mono text-xs font-bold text-[#006c49] dark:text-emerald-400">99.4% Paridad</span>
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-extrabold font-mono text-slate-900 dark:text-white">75%</span>
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Tasa Aprobación</span>
            </div>
            <div className="w-full h-1.5 rounded-full bg-slate-200 dark:bg-slate-700 mt-2 overflow-hidden">
              <div className="h-full bg-slate-900 dark:bg-slate-300 rounded-full" style={{ width: '75%' }} />
            </div>
            <div className="text-[10px] font-mono text-slate-500 dark:text-slate-400 mt-2">
              Muestra auditada: <strong>2,898 solicitudes</strong>
            </div>
          </div>

          {/* Region Guayana */}
          <div className="bg-slate-50/70 dark:bg-slate-900/60 rounded-xl border border-slate-200/60 dark:border-slate-800/80 p-4">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-800 dark:text-slate-200">Región Guayana</span>
              <span className="font-mono text-xs font-bold text-[#006c49] dark:text-emerald-400">98.2% Paridad</span>
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-extrabold font-mono text-slate-900 dark:text-white">73%</span>
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Tasa Aprobación</span>
            </div>
            <div className="w-full h-1.5 rounded-full bg-slate-200 dark:bg-slate-700 mt-2 overflow-hidden">
              <div className="h-full bg-slate-900 dark:bg-slate-300 rounded-full" style={{ width: '73%' }} />
            </div>
            <div className="text-[10px] font-mono text-slate-500 dark:text-slate-400 mt-2">
              Muestra auditada: <strong>1,940 solicitudes</strong>
            </div>
          </div>

        </div>

        {/* Bottom Legal Compliance Row */}
        <div className="mt-5 pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center gap-2 text-xs text-slate-600 dark:text-slate-400 font-medium">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
          <span>
            Cumplimiento estricto del Artículo 14 de la Ley de Inteligencia Artificial Gubernamental (No Discriminación Indirecta y Transparencia Algorítmica).
          </span>
        </div>

      </div>

      {/* Proof Modal */}
      <ProofModal
        isOpen={isProofModalOpen}
        onClose={() => setIsProofModalOpen(false)}
        recordId="Evaluación de Beca Estudiantil #894"
        sha256Hash={sha256VerificationHash}
        onCopy={handleCopy}
      />
    </div>
  );
};
