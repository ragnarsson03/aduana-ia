import React from 'react';
import { CanalSeguroFeature } from '../features/canal-seguro/CanalSeguroFeature';

interface CanalSeguroViewProps {
  onBackToPasarela: () => void;
  onNotify: (msg: string) => void;
  darkMode: boolean;
  onToggleDarkMode: () => void;
}

export const CanalSeguroView: React.FC<CanalSeguroViewProps> = ({
  onBackToPasarela,
  onNotify,
  darkMode,
  onToggleDarkMode,
}) => {
  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 transition-colors">
      <CanalSeguroFeature
        darkMode={darkMode}
        onToggleDarkMode={onToggleDarkMode}
        onNavigateHome={onBackToPasarela}
        onNotify={onNotify}
      />
    </div>
  );
};
