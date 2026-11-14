export interface ContactProfile {
  id: string;
  name: string;
  initials: string;
  role: string;
  isOnline: boolean;
  avatarBgColor?: string;
  badge?: string;
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
    isClassified: boolean;
  };
  maskedToken?: string;
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
}
