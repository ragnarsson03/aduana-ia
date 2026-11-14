import type { NavTabId } from './navigation';

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
  /** Pestañas permitidas, entregadas por el servidor (RBAC aduanero). */
  allowedTabs: NavTabId[];
  /** Pestaña inicial, entregada por el servidor. */
  defaultTab: NavTabId;
  /** Rol aduanero real (RBAC del backend). */
  aduanaRole?: string;
  credentials: UserCredentials;
  lastLogin?: string;
}
