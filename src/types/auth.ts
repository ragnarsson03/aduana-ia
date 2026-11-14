export type UserRole = 'analista' | 'administrador' | 'auditor';

export interface UserCredentials {
  clearanceLevel: string;
  entity: string;
  ed25519Key: string;
  ed25519Status: string;
  permissions: string[];
  sessionId: string;
  fingerprint: string;
  department?: string;
  idNumber?: string;
}

export interface AuthUser {
  id: string;
  name: string;
  shortName: string;
  role: UserRole;
  roleLabel: string;
  avatarText: string;
  email: string;
  status: 'online' | 'busy' | 'away';
  credentials: UserCredentials;
  lastLogin?: string;
}

export interface LoginCredentialPreset {
  role: UserRole;
  roleName: string;
  user: AuthUser;
  defaultPass: string;
  badgeColor: string;
  description: string;
}
