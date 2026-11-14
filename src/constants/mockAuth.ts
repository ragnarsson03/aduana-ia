import { AuthUser, LoginCredentialPreset, UserRole } from '../types/auth';
import { ContactProfile, InstitutionalChannel, ChatMessage } from '../types/secure-channel';
import { NavTabId } from '../types/navigation';

export const ROLE_ALLOWED_TABS: Record<UserRole, NavTabId[]> = {
  auditor: ['ledger', 'explicabilidad'],
  analista: ['pasarela', 'chat', 'canal'],
  administrador: ['pasarela', 'chat', 'ledger', 'explicabilidad', 'canal'],
};

export const ROLE_DEFAULT_TAB: Record<UserRole, NavTabId> = {
  auditor: 'ledger',
  analista: 'pasarela',
  administrador: 'pasarela',
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
  administrador: {
    id: 'usr-admin-03',
    name: 'Marcos Vivas',
    shortName: 'Marcos V.',
    role: 'administrador',
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
    role: 'administrador',
    roleName: 'Administrador de Infraestructura',
    user: MOCK_AUTH_USERS.administrador,
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

export const SAMPLE_PDF_DATA_URL = 'data:application/pdf;base64,JVBERi0xLjQKMSAwIG9iajw8L1R5cGUvQ2F0YWxvZy9QYWdlcyAyIDAgUj4+ZW5kb2JqCjIgMCBvYmo8PC9UeXBlL1BhZ2VzL0tpZHNbMyAwIFJdL0NvdW50IDE+PmVuZG9iagozIDAgb2JqPDwvVHlwZS9QYWdlL01lZGlhQm94WzAgMCAzMDAgMTQ0XS9QYXJlbnQgMiAwIFIvUmVzb3VyY2VzPDw+Pi9Db250ZW50cyA0IDAgUj4+ZW5kb2JqCjQgMCBvYmo8PC9MZW5ndGggNTU+PnN0cmVhbQpCVCAvRjEgMTIgVGYgNTAgMTAwIFRkIChBZHVhbmEgSUEgLSBEaWN0YW1lbiBPZmljaWFsKSBUaiBFVAplbmRzdHJlYW0KZW5kb2JqCnhyZWYKMCA1CjAwMDAwMDAwMDAgNjU1MzUgZiAKMDAwMDAwMDAxMCAwMDAwMCBuIAowMDAwMDAwMDYwIDAwMDAwIG4gCjAwMDAwMDAxMTcgMDAwMDAgbiAKMDAwMDAwMDIyMyAwMDAwMCBuIAp0cmFpbGVyPDwvU2l6ZSA1L1Jvb3QgMSAwIFI+PgpzdGFydHhyZWYKMzI4CiUlRU9G';

export const SAMPLE_CSV_DATA_URL = 'data:text/csv;charset=utf-8,Codigo,Mercancia,Peso_Kg,Arancel,Estado\nTR-001,Componentes_Electronicos,1450,12.5%,APROBADO\nTR-002,Insumos_Medicos,820,0.0%,EXENTO_SUBSIDIO\nTR-003,Material_Educativo,3200,0.0%,EXENTO_UNETI';

export const INITIAL_CHAT_MESSAGES: ChatMessage[] = [
  {
    id: 'msg-1',
    senderName: 'Carlos Méndez',
    senderInitials: 'CM',
    senderRole: 'Auditor Principal',
    isCurrentUser: false,
    timestamp: '14:22:10 UTC',
    content: 'Buenas tardes estimado operador. Estamos revisando la concordancia de expedientes en el bloque #004. Requerimos confirmar si el trámite reportado con subsidio tiene respaldo documental en el nodo local.',
    fileAttachment: {
      name: 'Dictamen_Auditoria_Previa_SENIAT_004.pdf',
      sizeBytes: 148520,
      formattedSize: '145.0 KB',
      mimeType: 'application/pdf',
      dataUrl: SAMPLE_PDF_DATA_URL,
      sha256Hex: '9f83c21a4e21b76a889312fe29ab430e7649d821390bf143528bca31a4f52631',
      isClassified: true,
    },
    cryptoVerification: {
      algorithm: 'AES-256-GCM + Gov-Ed25519',
      handshakeStatus: 'Validada y Activa en Enclave RAM',
      ed25519Key: '0x8F9...3B',
      ivHex: '4a1b8c2d9e0f1a2b3c4d5e6f',
      ciphertextPreview: '0x8f31c9a0d2e471b299c01a2b3c4d5e6f...',
      authTagValid: true,
      sha256Short: '9f83c21a4e...52631',
      piiShieldStatus: 'Protección Homomórfica Conforme',
      sessionTokenId: 'sec-992a-fed',
    }
  },
  {
    id: 'msg-2',
    senderName: 'Usted (Operador)',
    senderInitials: 'OP',
    senderRole: 'Operador de Guardia',
    isCurrentUser: true,
    timestamp: '14:25:34 UTC',
    content: 'Recibido, Carlos. Estoy consultando la pasarela de inferencia en memoria aislada. El sistema auditó una solicitud ciudadana hace pocos minutos.',
    verifiedDelivery: true,
    cryptoVerification: {
      algorithm: 'AES-256-GCM + Gov-Ed25519',
      handshakeStatus: 'Validada y Activa en Enclave RAM',
      ed25519Key: 'Enclave-RAM-Local',
      ivHex: 'e3b0c44298fc1c149afbf4c8',
      ciphertextPreview: '0x3c99f18a2bc4e578a109ca828190fe...',
      authTagValid: true,
      sha256Short: 'e3b0c44298...852b8',
      piiShieldStatus: 'Zero-Plaintext-PII en Memoria',
      sessionTokenId: 'sec-992a-fed',
    }
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
    piiHash: '89ab...7df1',
    cryptoVerification: {
      algorithm: 'AES-256-GCM + Gov-Ed25519',
      handshakeStatus: 'Validada y Activa en Enclave RAM',
      ed25519Key: '0x8F9...3B',
      ivHex: '89ab7df10012345678abcdef',
      ciphertextPreview: '0xd4e5f6a1b2c3d4e5f6a1b2c3d4e5f6...',
      authTagValid: true,
      sha256Short: '89ab7df100...cdef1',
      piiShieldStatus: 'Ofuscación Homomórfica Activa (Cédula)',
      sessionTokenId: 'sec-992a-fed',
    }
  },
  {
    id: 'msg-4',
    senderName: 'Usted (Operador)',
    senderInitials: 'OP',
    senderRole: 'Operador de Guardia',
    isCurrentUser: true,
    timestamp: '14:32:48 UTC',
    content: 'Confirmado. El token homomórfico quedó registrado en el bloque #002 con firma válida y cero fuga de datos personales en el modelo local Ollama. El dictamen fue emitido y archivado en el ledger.',
    verifiedDelivery: true,
    cryptoVerification: {
      algorithm: 'AES-256-GCM + Gov-Ed25519',
      handshakeStatus: 'Validada y Activa en Enclave RAM',
      ed25519Key: 'Enclave-RAM-Local',
      ivHex: '7f83b1657ff1fc53b92dc181',
      ciphertextPreview: '0x71d5e0a1b2c34d5e6f7a8b9c0d1e2f...',
      authTagValid: true,
      sha256Short: '7f83b1657f...069a1',
      piiShieldStatus: 'Sellado en Bloque Ledger #002',
      sessionTokenId: 'sec-992a-fed',
    }
  }
];

export const INITIAL_CONTACT_THREADS: Record<string, ChatMessage[]> = {
  'user-cm': INITIAL_CHAT_MESSAGES,
  'user-es': [
    {
      id: 'msg-es-1',
      senderName: 'Elena Salazar',
      senderInitials: 'ES',
      senderRole: 'Operadora de Guardia',
      isCurrentUser: false,
      timestamp: '14:05:12 UTC',
      content: 'Buenos días colega. Adjunto el manifiesto de carga aduanal consolidada del turno matutino para corroborar los rubros con exención arancelaria según baremo UNETI.',
      fileAttachment: {
        name: 'Manifiesto_Carga_Fronteriza_089.csv',
        sizeBytes: 38410,
        formattedSize: '37.5 KB',
        mimeType: 'text/csv',
        dataUrl: SAMPLE_CSV_DATA_URL,
        sha256Hex: '4a12b89c3140de21f1082a03cf84129b01019a583e761c56ad40f1a941e73928',
        isClassified: false,
      }
    },
    {
      id: 'msg-es-2',
      senderName: 'Usted (Operador)',
      senderInitials: 'OP',
      senderRole: 'Operador de Guardia',
      isCurrentUser: true,
      timestamp: '14:10:44 UTC',
      content: 'Recibido Elena. Verificando la concordancia de hashes y la firma Ed25519 de la Intendencia.',
      verifiedDelivery: true,
    }
  ],
  'user-mv': [
    {
      id: 'msg-mv-1',
      senderName: 'Marcos Vivas',
      senderInitials: 'MV',
      senderRole: 'Supervisor Ciberseguridad',
      isCurrentUser: false,
      timestamp: '13:42:00 UTC',
      content: 'Alerta de rutina: Se ejecutó la auditoría de nodos perimetrales. Todos los enclaves RAM mantienen sellos criptográficos intactos. Adjunto certificado de custodia actualizado.',
      fileAttachment: {
        name: 'Certificado_GovEd25519_Enclave.pem',
        sizeBytes: 1820,
        formattedSize: '1.8 KB',
        mimeType: 'application/x-pem-file',
        dataUrl: 'data:text/plain;charset=utf-8,-----BEGIN%20GOV-ED25519%20CERTIFICATE-----%0AMIICxDCCAaygAwIBAgIUQzM0...GOVTECH-ADUANA-IA-2026%0A-----END%20GOV-ED25519%20CERTIFICATE-----',
        sha256Hex: '2c7a5f33d45e0a6184918e93ba918451872a9128f645b23851082390a7b45129',
        isClassified: true,
      }
    }
  ],
  'user-ls': [
    {
      id: 'msg-ls-1',
      senderName: 'Lucía Santander',
      senderInitials: 'LS',
      senderRole: 'Auditora Legal Gov-AI',
      isCurrentUser: false,
      timestamp: '12:20:18 UTC',
      content: 'Estimado equipo: La consultoría legal aprobó los parámetros de explicabilidad algorítmica para el Art. 14 de la Ley IA. Adjunto dictamen legal oficial para su incorporación al Ledger.',
      fileAttachment: {
        name: 'Opinion_Juridica_Transparencia_Algoritmica.pdf',
        sizeBytes: 98200,
        formattedSize: '95.9 KB',
        mimeType: 'application/pdf',
        dataUrl: SAMPLE_PDF_DATA_URL,
        sha256Hex: '7b819c43d920ef182a5509ba01efc91823984019283746152019283746152019',
        isClassified: true,
      }
    }
  ],
  'user-cr': [
    {
      id: 'msg-cr-1',
      senderName: 'Dra. Carmen R.',
      senderInitials: 'DR',
      senderRole: 'Departamento y Confidencialidad',
      isCurrentUser: false,
      timestamp: '11:15:00 UTC',
      content: 'Recordatorio institucional: Todo trámite que incluya datos personales sensibles (médicos, tributarios o de filiación) debe transitar exclusivamente bajo ofuscación homomórfica en memoria confina.'
    }
  ],
  'auditoria-general': [
    {
      id: 'msg-ag-1',
      senderName: 'Canal Institucional',
      senderInitials: 'AG',
      senderRole: 'Sistema Central',
      isCurrentUser: false,
      timestamp: '08:00:00 UTC',
      content: 'Transmisión General: Nodo Central Aduana IA operando en régimen soberano Zero-Trust. 552 verificaciones criptográficas activas. Reportar cualquier desvío de hash al Supervisor de Guardia.'
    }
  ],
  'alertas-ledger': [
    {
      id: 'msg-al-1',
      senderName: 'Centinela Criptográfico',
      senderInitials: 'CC',
      senderRole: 'Daemon de Integridad',
      isCurrentUser: false,
      timestamp: '09:30:15 UTC',
      content: 'Bloques génesis a #004 validados con HMAC-SHA256. Ninguna discrepancia de integridad detectada en el enlace de bloques.'
    }
  ]
};
