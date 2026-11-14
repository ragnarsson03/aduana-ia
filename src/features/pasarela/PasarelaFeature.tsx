import React, { useState } from 'react';
import { HeroPipelineSection } from './components/HeroPipelineSection';
import { LedgerSummaryWidget } from './components/LedgerSummaryWidget';
import { ExplicaSummaryWidget } from './components/ExplicaSummaryWidget';
import { 
  INITIAL_PIPELINE_STAGES, 
  INITIAL_SHIELD_RULES, 
  SUMMARY_LEDGER_BLOCKS, 
  SCHOLARSHIP_DOSSIER 
} from '../../constants/mockData';

interface PasarelaFeatureProps {
  onNavigateToLedger?: () => void;
  onNavigateToExplica?: () => void;
  onNotify?: (msg: string) => void;
}

export const PasarelaFeature: React.FC<PasarelaFeatureProps> = ({
  onNavigateToLedger,
  onNavigateToExplica,
  onNotify,
}) => {
  const [stages, setStages] = useState(INITIAL_PIPELINE_STAGES);
  const [activeStageId, setActiveStageId] = useState('ia-local');

  const handleSelectStage = (id: string) => {
    setActiveStageId(id);
    const selected = stages.find(s => s.id === id);
    if (selected && onNotify) {
      onNotify(`Fase seleccionada: ${selected.name} ${selected.subtitle} — Estado: ${selected.status}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* 1. Hero Pipeline Section (Avila silhouette, 3 columns: Citizen Prompt, 5 stages, Shield Filter) */}
      <HeroPipelineSection
        stages={stages}
        rules={INITIAL_SHIELD_RULES}
        activeStageId={activeStageId}
        onSelectStage={handleSelectStage}
        latencyMs={142}
      />

      {/* 2. Dual Column Section: Ledger Summary (6 cols) + Explainability Summary (6 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        <div className="lg:col-span-6">
          <LedgerSummaryWidget
            blocks={SUMMARY_LEDGER_BLOCKS}
            onViewFullLedger={onNavigateToLedger}
          />
        </div>

        <div className="lg:col-span-6">
          <ExplicaSummaryWidget
            dossier={SCHOLARSHIP_DOSSIER}
            onViewFullExplica={onNavigateToExplica}
          />
        </div>
      </div>
    </div>
  );
};
