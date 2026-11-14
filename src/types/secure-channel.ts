export interface ContactCredentials {
  clearanceLevel: string;
  entity: string;
  ed25519Key: string;
  ed25519Status: string;
  permissions: string[];
  sessionId: string;
  department: string;
  idNumber: string;
}

export interface ContactProfile {
  id: string;
  name: string;
  initials: string;
  role: string;
  isOnline: boolean;
  avatarBgColor?: string;
  badge?: string;
  hasGreenDot?: boolean;
  time?: string;
  unreadCount?: number;
  credentials?: ContactCredentials;
}

export interface InstitutionalChannel {
  id: string;
  name: string;
  badgeCount?: number;
  hasAlertDot?: boolean;
  alertDotColor?: string;
  description: string;
}

export interface FileAttachment {
  name: string;
  sizeBytes: number;
  formattedSize: string;
  mimeType: string;
  dataUrl: string;
  sha256Hex: string;
  isClassified?: boolean;
}

export interface CryptoProcessVerification {
  algorithm: string;
  handshakeStatus: string;
  ed25519Key: string;
  ivHex: string;
  ciphertextPreview: string;
  authTagValid: boolean;
  sha256Short: string;
  piiShieldStatus: string;
  sessionTokenId: string;
}

export interface ChatMessage {
  id: string;
  senderName: string;
  senderInitials?: string;
  senderRole?: string;
  isCurrentUser?: boolean;
  isSystem?: boolean;
  timestamp: string;
  content: string;
  piiMasked?: boolean;
  piiType?: string;
  piiHash?: string;
  verifiedDelivery?: boolean;
  maskedToken?: string;
  tokenExampleLabel?: string;
  secondTimestamp?: string;
  sentReceiptLabel?: string;
  fileAttachment?: FileAttachment;
  cryptoVerification?: CryptoProcessVerification;
  attachment?: {
    title: string;
    description: string;
    code?: string;
    isClassified: boolean;
  };
}

export interface AuditorUserProfile {
  initials: string;
  name: string;
  badgeRole: string;
  idNumber: string;
  clearanceLevel: string;
  department: string;
  ed25519Status: string;
  permissionsSummary: string;
  verifiedBadgeText?: string;
}
