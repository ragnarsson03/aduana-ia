import React from 'react';
import { CanalSeguroFeature } from '../features/canal-seguro/CanalSeguroFeature';

interface CanalSeguroViewProps {
  onBackToPasarela: () => void;
  onNotify: (msg: string) => void;
}

export const CanalSeguroView: React.FC<CanalSeguroViewProps> = ({
  onBackToPasarela,
  onNotify,
}) => {
  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 transition-colors">
      <CanalSeguroFeature
        onBackToPasarela={onBackToPasarela}
        onNotify={onNotify}
      />
    </div>
  );
};
