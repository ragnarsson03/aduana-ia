import React from 'react';
import { IncomingPromptCard } from './IncomingPromptCard';
import { PipelineStageNodes } from './PipelineStageNodes';
import { PipelineProgressBar } from './PipelineProgressBar';
import { ShieldFilterCard } from './ShieldFilterCard';
import { AVILA_MOUNTAIN_PATH } from '../../../constants/theme';
import { PipelineStageConfig, ShieldRuleMapping } from '../../../types';

interface HeroPipelineSectionProps {
  stages: PipelineStageConfig[];
  rules: ShieldRuleMapping[];
  activeStageId?: string;
  onSelectStage?: (id: string) => void;
  latencyMs?: number;
}

export const HeroPipelineSection: React.FC<HeroPipelineSectionProps> = ({
  stages,
  rules,
  activeStageId = 'ia-local',
  onSelectStage,
  latencyMs = 142,
}) => {
  return (
    <section 
      className="relative overflow-hidden rounded-3xl bg-gradient-to-b from-white via-slate-50/60 to-white dark:from-slate-900 dark:via-slate-900/90 dark:to-[#0b0f19] border border-slate-200/90 dark:border-slate-800 shadow-xs p-5 sm:p-6 lg:p-8 transition-colors"
      data-purpose="inference-pipeline"
    >
      {/* Avila Mountain Subtle Silhouettes (Vector Decorative) */}
      <div className="absolute inset-x-0 bottom-0 top-12 pointer-events-none opacity-20 dark:opacity-10 flex items-end justify-center overflow-hidden">
        <svg 
          className="w-full h-48 min-w-[900px] text-slate-400 dark:text-slate-600" 
          fill="currentColor" 
          viewBox="0 0 1200 240"
        >
          <path d={AVILA_MOUNTAIN_PATH} />
        </svg>
      </div>

      {/* Upper subtle floating status aesthetic */}
      <div className="relative z-10 flex justify-center mb-6">
        <div className="inline-flex items-center gap-2 px-3 py-1 bg-white/80 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 rounded-full shadow-2xs text-xs text-slate-600 dark:text-slate-400 backdrop-blur-xs font-mono">
          <span className="inline-block w-2 h-2 rounded-full bg-[#4f46e5] animate-ping" />
          <span>Supervisión en tiempo real activa • Latencia E2E: {latencyMs}ms</span>
        </div>
      </div>

      {/* Pipeline Central Flow: Left Sanitized Input, Core Nodes, and Right Shield Filter */}
      <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-5 sm:gap-6 items-stretch">
        
        {/* Column 1: Citizen Prompt Sanitization Card (3 cols) */}
        <div className="lg:col-span-3 flex">
          <IncomingPromptCard />
        </div>

        {/* Column 2: The 5 Pipeline Core Stages + Progress Bar (6 cols) */}
        <div className="lg:col-span-6 flex flex-col justify-between">
          <PipelineStageNodes 
            stages={stages} 
            activeStageId={activeStageId} 
            onSelectStage={onSelectStage} 
          />
          <PipelineProgressBar 
            completedStepCount={4} 
            totalSteps={5}
            sublabel="80% completado (Fase Guard-Out)"
          />
        </div>

        {/* Column 3: Shield Filter Summary Card (3 cols) */}
        <div className="lg:col-span-3 flex">
          <ShieldFilterCard 
            rules={rules} 
            promptRiskPercentage={8}
            riskLevelLabel="8% (Nivel Seguro)"
          />
        </div>

      </div>
    </section>
  );
};
