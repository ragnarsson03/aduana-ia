export interface ContactProfile {
  id: string;
  name: string;
  initials: string;
  role: string;
  isOnline: boolean;
  avatarBgColor?: string;
  badge?: string;
  hasGreenDot?: boolean;
}

export interface ChatMessage {
  id: string;
  senderName: string;
  senderInitials?: string;
  isSystem: boolean;
  timestamp: string;
  content: string;
  attachment?: {
    title: string;
    description: string;
    code?: string;
    isClassified: boolean;
  };
  maskedToken?: string;
  tokenExampleLabel?: string;
  secondTimestamp?: string;
  sentReceiptLabel?: string;
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
