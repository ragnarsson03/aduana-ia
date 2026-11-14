export type PipelineStageStatus = 'pending' | 'active' | 'completed' | 'blocked';

export interface PipelineStageConfig {
  id: string;
  name: string;
  subtitle: string;
  iconName: 'shield' | 'lock' | 'cpu' | 'log-out' | 'database';
  status: PipelineStageStatus;
  order: number;
}

export interface ShieldRuleMapping {
  original: string;
  masked: string;
  type: string;
}

export interface PipelineSimulationState {
  currentStepIndex: number; // 0 to 4
  completionPercentage: number;
  currentPhaseName: string;
  latencyMs: number;
  isRealTimeActive: boolean;
  promptRiskPercentage: number;
  riskLevelLabel: string;
  incomingPrompt: {
    citizenText: string;
    sanitizedTokens: string[];
    tokenVersion: string;
    piiStatus: string;
  };
  rules: ShieldRuleMapping[];
}
