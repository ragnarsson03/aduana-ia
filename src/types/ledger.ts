export type BlockStatus = 'verified' | 'corrupted' | 'tampered';

export interface AuditBlock {
  index: number;
  blockNumber: string;
  title: string;
  status: BlockStatus;
  statusLabel: string;
  timestamp: string;
  timeRange: string;
  sha256Hash: string;
  ed25519Signature: string;
  expectedHash?: string;
  discrepancyNote?: string;
  purpose?: string;
  isGenesis?: boolean;
}

export interface LedgerMetrics {
  totalBlocks: number;
  sealingFrequency: string;
  authorizedSignatures: string;
  chainStatus: 'isolated' | 'synchronized' | 'validating';
  validBlocksCount: number;
}
