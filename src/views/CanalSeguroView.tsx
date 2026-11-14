import React from 'react';
import { CanalSeguroFeature } from '../features/canal-seguro/CanalSeguroFeature';
import { AuthUser } from '../types/auth';

interface CanalSeguroViewProps {
  currentUser?: AuthUser;
  onBackToPasarela: () => void;
  onNotify: (msg: string) => void;
  darkMode: boolean;
  onToggleDarkMode: () => void;
}

export const CanalSeguroView: React.FC<CanalSeguroViewProps> = ({
  currentUser,
  onBackToPasarela,
  onNotify,
  darkMode,
  onToggleDarkMode,
}) => {
  return (
    <div className="w-full max-w-7xl mx-auto px-2 sm:px-4 lg:px-6 py-3 sm:py-5 transition-colors">
      <CanalSeguroFeature
        currentUser={currentUser}
        darkMode={darkMode}
        onToggleDarkMode={onToggleDarkMode}
        onNavigateHome={onBackToPasarela}
        onNotify={onNotify}
      />
    </div>
  );
};
