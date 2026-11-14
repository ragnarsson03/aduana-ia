import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { api } from '../services/apiClient';
import type { GatewayProcessResponse } from '../types/api';

export type ConnectionState = 'checking' | 'online' | 'offline';

interface BackendStatusValue {
  connection: ConnectionState;
  /** Último resultado real de /gateway/process (solo en memoria, jamás persistido). */
  lastResult: GatewayProcessResponse | null;
  setLastResult: (result: GatewayProcessResponse | null) => void;
  recheck: () => void;
}

const HEALTH_POLL_MS = 15000;

const BackendStatusContext = createContext<BackendStatusValue>({
  connection: 'checking',
  lastResult: null,
  setLastResult: () => undefined,
  recheck: () => undefined,
});

export const BackendStatusProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [connection, setConnection] = useState<ConnectionState>('checking');
  const [lastResult, setLastResult] = useState<GatewayProcessResponse | null>(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let cancelled = false;
    const check = async () => {
      try {
        await api.getHealth();
        if (!cancelled) setConnection('online');
      } catch {
        if (!cancelled) setConnection('offline');
      }
    };
    void check();
    const id = setInterval(check, HEALTH_POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [tick]);

  const recheck = useCallback(() => setTick((n) => n + 1), []);
  const value = useMemo(
    () => ({ connection, lastResult, setLastResult, recheck }),
    [connection, lastResult, recheck]
  );
  return <BackendStatusContext.Provider value={value}>{children}</BackendStatusContext.Provider>;
};

export const useBackendStatus = (): BackendStatusValue => useContext(BackendStatusContext);
