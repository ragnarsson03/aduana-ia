import { ContactProfile, InstitutionalChannel, ChatMessage } from '../types/secure-channel';

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
