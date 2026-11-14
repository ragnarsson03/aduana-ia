import React from 'react';
import { GatewayConsole } from './components/GatewayConsole';
import { useBackendStatus } from '../../state/BackendStatus';

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
  const { connection } = useBackendStatus();

  if (connection === 'checking') {
    return (
      <p role="status" data-testid="connection-checking" className="text-sm text-slate-500">
        Comprobando conexión con el servidor…
      </p>
    );
  }

  // Con conexión: datos reales del backend, sin mockData.
  if (connection === 'online') {
    return (
      <GatewayConsole
        onNavigateToLedger={onNavigateToLedger}
        onNavigateToExplica={onNavigateToExplica}
        onNotify={onNotify}
      />
    );
  }

  return (
    <div className="rounded-2xl border border-amber-200 dark:border-amber-900/50 bg-amber-50 dark:bg-amber-950/30 p-6 text-sm text-amber-900 dark:text-amber-200">
      Sin conexión con el servidor backend. Inicie el servicio para operar la Pasarela Soberana.
    </div>
  );
};
