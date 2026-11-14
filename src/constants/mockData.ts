import { 
  PipelineStageConfig, 
  ShieldRuleMapping, 
  AuditBlock, 
  ScholarshipEvaluationDossier, 
  ContactProfile, 
  ChatMessage, 
  AuditorUserProfile 
} from '../types';

export const INITIAL_PIPELINE_STAGES: PipelineStageConfig[] = [
  { id: 'shield', name: 'Shield', subtitle: '(Anonimización)', iconName: 'shield', status: 'completed', order: 1 },
  { id: 'guard-in', name: 'Guard-In', subtitle: '(Seguridad)', iconName: 'lock', status: 'completed', order: 2 },
  { id: 'ia-local', name: 'IA Local', subtitle: '(Ollama)', iconName: 'cpu', status: 'active', order: 3 },
  { id: 'guard-out', name: 'Guard-Out', subtitle: '(Salida)', iconName: 'log-out', status: 'completed', order: 4 },
  { id: 'ledger', name: 'Ledger', subtitle: '(Auditoría)', iconName: 'database', status: 'pending', order: 5 },
];

export const INITIAL_SHIELD_RULES: ShieldRuleMapping[] = [
  { original: 'V-XXXXXXX', masked: 'V-XXXXXXX', type: 'Cédula SAIME' },
  { original: '041X-XXXXXXX', masked: '041X-XXXXXXX', type: 'Teléfono Móvil' },
  { original: '@correo.ve', masked: '@correo.ve', type: 'Dominio Oficial' },
  { original: 'Cuentas 20 Dig.', masked: 'Ofuscado', type: 'Cuentas Bancarias' },
];

export const SUMMARY_LEDGER_BLOCKS: AuditBlock[] = [
  {
    index: 4,
    blockNumber: '#004',
    title: 'Maskd summary',
    status: 'verified',
    statusLabel: 'Verified',
    timestamp: '1:33 AM',
    timeRange: '1:33 AM / 2:30 AM',
    sha256Hash: '...a2e3e63aaaab67e3ea908c6ff998124b817...',
    ed25519Signature: '4425554842a8856e34.48c1a... (Validada)',
  },
  {
    index: 4,
    blockNumber: '#004',
    title: 'Integridad Rota — Hash No Coincide',
    status: 'corrupted',
    statusLabel: 'ALERTA',
    timestamp: '1:33 AM',
    timeRange: '1:33 AM / 2:30 AM',
    sha256Hash: '....85772833...2b2e280e5... [Mismatch Detectado]',
    ed25519Signature: '452555199533425327.4... Firma no coincide con bloque previo',
    discrepancyNote: 'Mismatch Detectado',
  },
  {
    index: 3,
    blockNumber: '#003',
    title: 'Maskd summary',
    status: 'verified',
    statusLabel: 'Verified',
    timestamp: '1:33 AM',
    timeRange: '1:33 AM / 3:30 PM',
    sha256Hash: '....a336ba5ocRa6ao61ea...',
    ed25519Signature: 'A74d45hd3d33c55014.4 (Válido)',
  },
];

export const SCHOLARSHIP_DOSSIER: ScholarshipEvaluationDossier = {
  expedienteId: 'SOL-2026-894',
  applicantName: 'Camila Rivas',
  academicRecordId: '2025-8E',
  major: 'Ingeniería en Telecomunicaciones',
  score: 78,
  maxScore: 100,
  minimumThreshold: 65,
  verdictLabel: 'Aprobado',
  aiVerdict: 'Aprobada (94.6% Confianza)',
  humanAuditorVerdict: 'Aprobada (L. Santander DGA-08)',
  concordanceLabel: '100% Homogénea',
  impactDisparityRatio: '0.98 / 1.00',
  parityBadgeText: 'Paridad 99.4%',
  variables: [
    { id: 'v1', name: 'Promedio Académico (18.6 / 20)', displayValue: '+34%', weightPercentage: 34, isPositive: true, barWidthPercentage: 78 },
    { id: 'v2', name: 'Situación Socioeconómica', displayValue: '+28%', weightPercentage: 28, isPositive: true, barWidthPercentage: 64 },
    { id: 'v3', name: 'Distancia Geográfica (Zona Foránea)', displayValue: '+16%', weightPercentage: 16, isPositive: true, barWidthPercentage: 42 },
    { id: 'v4', name: 'Factor de Disponibilidad Presupuestaria', displayValue: '-16%', weightPercentage: 16, isPositive: false, barWidthPercentage: 36 },
  ],
  regions: [
    { regionName: 'Región Central', approvalRate: 76, parityPercentage: 99.1, auditedSampleCount: 4120 },
    { regionName: 'Región Occidental', approvalRate: 74, parityPercentage: 98.8, auditedSampleCount: 3450 },
    { regionName: 'Región Oriental', approvalRate: 75, parityPercentage: 99.4, auditedSampleCount: 2898 },
    { regionName: 'Región Guayana', approvalRate: 73, parityPercentage: 98.2, auditedSampleCount: 1940 },
  ],
};

export const CONTACT_PROFILES: ContactProfile[] = [
  { id: 'c1', name: 'Dra. Carmen R.', initials: 'DR', role: 'Departamento y Confidencial...', isOnline: true, avatarBgColor: 'bg-amber-100 text-amber-800 dark:bg-amber-900/60 dark:text-amber-300' },
  { id: 'c2', name: 'Ing. Alejandro V.', initials: 'ING', role: 'Departamento y Control IA...', isOnline: true, avatarBgColor: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/60 dark:text-emerald-300' },
  { id: 'c3', name: 'Ing. Alejandro T.', initials: 'II', role: 'Departamento y Confidencial...', isOnline: true, avatarBgColor: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300' },
  { id: 'c4', name: 'Ing. Alejandro V.', initials: 'MG', role: 'Departamento y Confidencial...', isOnline: true, avatarBgColor: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/60 dark:text-indigo-300' },
  { id: 'c5', name: 'Dra. Madirin H.', initials: 'INI', role: 'Departamento y Confidencial...', isOnline: true, avatarBgColor: 'bg-teal-100 text-teal-800 dark:bg-teal-900/60 dark:text-teal-300' },
];

export const AUDITOR_USER_PROFILE: AuditorUserProfile = {
  initials: 'CM',
  name: 'Carlos Méndez',
  badgeRole: 'Auditor Principal',
  idNumber: 'ID: 0x8F9...3B',
  clearanceLevel: 'Nivel 4 — Confidencial Estatal',
  department: 'Ministerio de Tecnología e Innovación / UNETI',
  ed25519Status: 'Validada y Activa',
  permissionsSummary: 'Desencriptación de PII autorizada, Auditoría de Ledger y Supervisión de Modelos Locales.',
};

export const INITIAL_CHAT_MESSAGES: ChatMessage[] = [
  {
    id: 'm1',
    senderName: 'Auditor_Sistema',
    isSystem: true,
    timestamp: '1:33 AM',
    content: 'Documentación compartida para el análisis del expediente cónsono.',
    attachment: {
      title: '[DOCUMENTO CLASIFICADO — EXP-2026-99.pdf]',
      description: 'Documento sensible protegido por Aduana IA',
      isClassified: true,
    },
  },
  {
    id: 'm2',
    senderName: 'Dra. Carmen R.',
    senderInitials: 'DR',
    isSystem: false,
    timestamp: '2:37 AM',
    content: 'El expediente contiene datos protegidos bajo la ley de privacidad digital.',
  },
  {
    id: 'm3',
    senderName: 'Auditor_Sistema',
    isSystem: true,
    timestamp: '2:37 AM',
    content: 'Ejemplo de PII enmascarado automáticamente:',
    maskedToken: '[CÉDULA OCULTA]',
  },
];
