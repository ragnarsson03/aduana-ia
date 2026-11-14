import { AuthUser, LoginCredentialPreset, UserRole } from '../types/auth';
import { ContactProfile, InstitutionalChannel, ChatMessage } from '../types/secure-channel';
import { NavTabId } from '../types/navigation';

export const ROLE_ALLOWED_TABS: Record<UserRole, NavTabId[]> = {
  auditor: ['ledger', 'explicabilidad'],
  analista: ['pasarela', 'chat', 'canal'],
  admin: ['pasarela', 'chat', 'ledger', 'explicabilidad', 'canal'],
};

export const ROLE_DEFAULT_TAB: Record<UserRole, NavTabId> = {
  auditor: 'ledger',
  analista: 'pasarela',
  admin: 'pasarela',
};

export const MOCK_AUTH_USERS: Record<string, AuthUser> = {
  auditor: {
    id: 'usr-auditor-01',
    name: 'Deykary González',
    shortName: 'Deykary G.',
    role: 'auditor',
    roleLabel: 'Auditora Principal',
    avatarText: 'DG',
    email: 'auditor@aduana.gob.ve',
    status: 'online',
    credentials: {
      clearanceLevel: 'Nivel 4 — Confidencial Estatal',
      entity: 'Superintendencia Nacional Aduanera / Contraloría GovTech',
      ed25519Key: '0x8F9a...3B42',
      ed25519Status: 'Validada y Activa',
      permissions: [
        'Desencriptación de PII autorizada',
        'Auditoría de Ledger SHA-256',
        'Inspección de Inferencia GovEval',
        'Canal E2EE Enclave Seguro'
      ],
      sessionId: 'sec-992a-fed',
      fingerprint: 'sha256:8f9a2c16...d402',
      department: 'Dirección de Auditoría Algorítmica y Cumplimiento',
      idNumber: 'ID: 0x8F9...3B'
    },
    lastLogin: '14 Feb 2026, 14:15 UTC'
  },
  analista: {
    id: 'usr-analista-02',
    name: 'Elena Salazar',
    shortName: 'Elena S.',
    role: 'analista',
    roleLabel: 'Analista de Operaciones & Solvencias',
    avatarText: 'ES',
    email: 'analista@aduana.gob.ve',
    status: 'online',
    credentials: {
      clearanceLevel: 'Nivel 2 — Operativo Aduanero',
      entity: 'Intendencia Nacional de Aduanas / División de Trámites',
      ed25519Key: '0x3C4b...9F11',
      ed25519Status: 'Validada y Activa',
      permissions: [
        'Consulta de Pasarela en Tiempo Real',
        'Sanitización Homomórfica de PII',
        'Evaluación de Explicabilidad y Equidad',
        'Revisión de Declaraciones Aduaneras'
      ],
      sessionId: 'sec-441b-ops',
      fingerprint: 'sha256:3c4b8109...ef88',
      department: 'Departamento de Solvencias Fiscales y Aforo',
      idNumber: 'ID: 0x3C4...9F'
    },
    lastLogin: '14 Feb 2026, 14:12 UTC'
  },
  admin: {
    id: 'usr-admin-03',
    name: 'Marcos Vivas',
    shortName: 'Marcos V.',
    role: 'admin',
    roleLabel: 'Administrador de Infraestructura & Ciberseguridad',
    avatarText: 'MV',
    email: 'admin@aduana.gob.ve',
    status: 'online',
    credentials: {
      clearanceLevel: 'Nivel 5 — Soberanía Crítica GovTech',
      entity: 'Centro Nacional de Ciberseguridad / Red Nacional de Integridad',
      ed25519Key: '0xE4A1...77C0',
      ed25519Status: 'Custodio Maestro Gov-Ed25519',
      permissions: [
        'Control Total de Nodos y Consenso',
        'Simulación de Manipulación y Cuarentena',
        'Gestión de Claves Criptográficas y Enclaves',
        'Supervisión Perimetral ISO/IEC 27001'
      ],
      sessionId: 'sec-001a-root',
      fingerprint: 'sha256:e4a112fc...77c0',
      department: 'Coordinación Nacional de Infraestructura Soberana',
      idNumber: 'ID: 0xE4A...C0'
    },
    lastLogin: '14 Feb 2026, 13:50 UTC'
  }
};

export const LOGIN_PRESETS: LoginCredentialPreset[] = [
  {
    role: 'auditor',
    roleName: 'Auditor',
    user: MOCK_AUTH_USERS.auditor,
    defaultPass: 'auditor2026',
    badgeColor: 'border-indigo-500/30 bg-indigo-50/70 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300',
    description: 'Módulos asignados: Explicabilidad y Ledger inalterable SHA-256.'
  },
  {
    role: 'analista',
    roleName: 'Analista',
    user: MOCK_AUTH_USERS.analista,
    defaultPass: 'analista2026',
    badgeColor: 'border-emerald-500/30 bg-emerald-50/70 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300',
    description: 'Módulos asignados: Pasarela, Nexus IA y Canal Seguro E2EE.'
  },
  {
    role: 'admin',
    roleName: 'Administrador de Infraestructura',
    user: MOCK_AUTH_USERS.admin,
    defaultPass: 'admin2026',
    badgeColor: 'border-amber-500/30 bg-amber-50/70 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300',
    description: 'Módulos asignados: Control total perimetral (Todos los módulos).'
  }
];

export const MOCK_CHANNELS: InstitutionalChannel[] = [
  {
    id: 'auditoria-general',
    name: 'auditoria-general',
    badgeCount: 12,
    description: 'Canal general de trazabilidad, concordancia de expedientes y dictámenes soberanos.'
  },
  {
    id: 'alertas-ledger',
    name: 'alertas-ledger',
    hasAlertDot: true,
    alertDotColor: 'bg-amber-500',
    description: 'Monitoreo de desajustes hash SHA-256, firmas no concordantes y aislamiento de nodos.'
  }
];

export const MOCK_CONTACTS_WITH_CREDENTIALS: ContactProfile[] = [
  {
    id: 'user-cm',
    name: 'Carlos Méndez',
    initials: 'CM',
    role: 'Auditor Principal',
    isOnline: true,
    avatarBgColor: 'bg-primary/10 dark:bg-primary/20 text-primary',
    time: '14:38',
    unreadCount: 0,
    credentials: {
      clearanceLevel: 'Nivel 4 — Confidencial Estatal',
      entity: 'Ministerio de Tecnología e Innovación / UNETI',
      ed25519Key: '0x8F9...3B',
      ed25519Status: 'Validada y Activa',
      permissions: [
        'Desencriptación de PII autorizada',
        'Auditoría de Ledger SHA-256',
        'Emisión de Dictámenes Vinculantes',
        'Inspección de Pasarela Local'
      ],
      sessionId: 'sec-992a-fed',
      department: 'División de Auditoría Forense y Ciberseguridad',
      idNumber: 'ID: 0x8F9...3B'
    }
  },
  {
    id: 'user-es',
    name: 'Elena Salazar',
    initials: 'ES',
    role: 'Operadora de Guardia',
    isOnline: true,
    avatarBgColor: 'bg-neutral-200 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300',
    time: '14:12',
    credentials: {
      clearanceLevel: 'Nivel 2 — Operativo Aduanero',
      entity: 'Intendencia Nacional de Aduanas / Operaciones',
      ed25519Key: '0x3C4...9F',
      ed25519Status: 'Validada y Activa',
      permissions: [
        'Gestión de Peticiones Ciudadanas',
        'Sanitización de PII con Shield',
        'Consulta de Constancias de Solvencia'
      ],
      sessionId: 'sec-441b-ops',
      department: 'Centro de Comando Operativo Aduanero',
      idNumber: 'ID: 0x3C4...9F'
    }
  },
  {
    id: 'user-mv',
    name: 'Marcos Vivas',
    initials: 'MV',
    role: 'Supervisor Ciberseguridad',
    isOnline: true,
    avatarBgColor: 'bg-neutral-200 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300',
    time: '13:50',
    unreadCount: 2,
    credentials: {
      clearanceLevel: 'Nivel 5 — Soberanía Crítica GovTech',
      entity: 'Centro Nacional de Ciberseguridad / Red de Integridad',
      ed25519Key: '0xE4A...C0',
      ed25519Status: 'Custodio Maestro Gov-Ed25519',
      permissions: [
        'Control de Nodos Perimetrales',
        'Simulación de Manipulación Criptográfica',
        'Aislamiento Preventivo de Memoria',
        'Gestión de Certificados Homomórficos'
      ],
      sessionId: 'sec-001a-root',
      department: 'Seguridad Ofensiva y Enclaves Confinados',
      idNumber: 'ID: 0xE4A...C0'
    }
  },
  {
    id: 'user-ls',
    name: 'Lucía Santander',
    initials: 'LS',
    role: 'Auditora Legal Gov-AI',
    isOnline: true,
    avatarBgColor: 'bg-neutral-200 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300',
    time: '12:35',
    credentials: {
      clearanceLevel: 'Nivel 3 — Dictamen Jurídico',
      entity: 'Consultoría Jurídica de Inteligencia Artificial Gubernamental',
      ed25519Key: '0x71D...5E',
      ed25519Status: 'Validada y Activa',
      permissions: [
        'Validación de Concordancia Legal ENISA',
        'Supervisión del Artículo 14 Ley IA',
        'Firma de Dictamen Vinculante'
      ],
      sessionId: 'sec-312c-leg',
      department: 'Marco Regulatorio y Transparencia Pública',
      idNumber: 'ID: 0x71D...5E'
    }
  },
  {
    id: 'user-cr',
    name: 'Dra. Carmen R.',
    initials: 'DR',
    role: 'Departamento y Confidencialidad',
    isOnline: false,
    avatarBgColor: 'bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300',
    credentials: {
      clearanceLevel: 'Nivel 4 — Confidencial Estatal',
      entity: 'SENIAT / Gerencia de Fiscalización Nacional',
      ed25519Key: '0xA92...F1',
      ed25519Status: 'Validada y Activa',
      permissions: [
        'Desencriptación Selectiva Homomórfica',
        'Custodia de Datos Ciudadanos'
      ],
      sessionId: 'sec-819a-fis',
      department: 'Departamento de Cumplimiento Normativo',
      idNumber: 'ID: 0xA92...F1'
    }
  }
];

export const INITIAL_CHAT_MESSAGES: ChatMessage[] = [
  {
    id: 'msg-1',
    senderName: 'Carlos Méndez',
    senderInitials: 'CM',
    senderRole: 'Auditor Principal',
    isCurrentUser: false,
    timestamp: '14:22:10 UTC',
    content: 'Buenas tardes estimado operador. Estamos revisando la concordancia de expedientes en el bloque #004. Requerimos confirmar si el trámite reportado con subsidio tiene respaldo documental en el nodo local.'
  },
  {
    id: 'msg-2',
    senderName: 'Usted (Operador)',
    senderInitials: 'OP',
    senderRole: 'Operador de Guardia',
    isCurrentUser: true,
    timestamp: '14:25:34 UTC',
    content: 'Recibido, Carlos. Estoy consultando la pasarela de inferencia en memoria aislada. El sistema auditó una solicitud ciudadana hace pocos minutos.',
    verifiedDelivery: true
  },
  {
    id: 'msg-3',
    senderName: 'Carlos Méndez',
    senderInitials: 'CM',
    senderRole: 'Auditor Principal',
    isCurrentUser: false,
    timestamp: '14:30:15 UTC',
    content: 'El contribuyente envió su consulta con la identificación [CÉDULA OCULTA] y solicitó constancia de solvencia fiscal inmediata. Favor verificar si el guardián de privacidad generó el token homomórfico correspondiente.',
    piiMasked: true,
    piiType: 'CÉDULA OCULTA',
    piiHash: '89ab...7df1'
  },
  {
    id: 'msg-4',
    senderName: 'Usted (Operador)',
    senderInitials: 'OP',
    senderRole: 'Operador de Guardia',
    isCurrentUser: true,
    timestamp: '14:32:48 UTC',
    content: 'Confirmado. El token homomórfico quedó registrado en el bloque #002 con firma válida y cero fuga de datos personales en el modelo local Ollama. El dictamen fue emitido y archivado en el ledger.',
    verifiedDelivery: true
  }
];
