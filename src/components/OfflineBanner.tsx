import React from 'react';
import { WifiOff } from 'lucide-react';
import { useBackendStatus } from '../state/BackendStatus';

export const OfflineBanner: React.FC = () => {
  const { connection } = useBackendStatus();
  if (connection !== 'offline') return null;
  return (
    <div
      role="alert"
      data-testid="offline-banner"
      className="flex items-center justify-center gap-2 px-4 py-2 text-xs font-semibold bg-amber-100 text-amber-900 dark:bg-amber-900/40 dark:text-amber-100 border-b border-amber-300 dark:border-amber-700"
    >
      <WifiOff className="w-4 h-4 shrink-0" aria-hidden="true" />
      <span>Sin conexión al servidor: datos simulados</span>
    </div>
  );
};
