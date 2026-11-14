import React from 'react';
import { PasarelaFeature } from '../features/pasarela/PasarelaFeature';

interface PasarelaViewProps {
  onNavigateToLedger: () => void;
  onNavigateToExplica: () => void;
  onNotify: (msg: string) => void;
}

export const PasarelaView: React.FC<PasarelaViewProps> = ({
  onNavigateToLedger,
  onNavigateToExplica,
  onNotify,
}) => {
  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 transition-colors">
      <PasarelaFeature
        onNavigateToLedger={onNavigateToLedger}
        onNavigateToExplica={onNavigateToExplica}
        onNotify={onNotify}
      />
    </div>
  );
};
