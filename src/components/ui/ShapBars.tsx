import React from 'react';
import { FEATURE_LABELS } from '../../utils/gatewayForm';
import type { ExplicaFeatureName } from '../../types/api';

interface ShapBarsProps {
  values: Record<string, number>;
  testIdPrefix: string;
}

const HALF = 100;

/** Barras divergentes en SVG (sin estilos en línea: la CSP del servidor los bloquea). */
export const ShapBars: React.FC<ShapBarsProps> = ({ values, testIdPrefix }) => {
  const entries = Object.entries(values);
  const maxAbs = Math.max(0.0001, ...entries.map(([, v]) => Math.abs(v)));
  return (
    <ul className="space-y-2" data-testid={`${testIdPrefix}-list`}>
      {entries.map(([name, value]) => {
        const w = (Math.abs(value) / maxAbs) * HALF;
        const positive = value >= 0;
        const label = FEATURE_LABELS[name as ExplicaFeatureName] ?? name;
        return (
          <li key={name} className="flex flex-wrap items-center gap-3 text-xs" data-testid={`${testIdPrefix}-${name}`}>
            <span className="w-56 shrink-0 text-slate-700 dark:text-slate-300">{label}</span>
            <svg width={HALF * 2} height="12" role="img" aria-label={`${label}: ${value.toFixed(4)}`} className="shrink-0">
              <rect x={HALF} y="0" width="1" height="12" className="fill-slate-400" />
              <rect
                x={positive ? HALF : HALF - w}
                y="2"
                width={w}
                height="8"
                className={positive ? 'fill-emerald-500' : 'fill-rose-500'}
              />
            </svg>
            <span className="font-mono tabular-nums text-slate-800 dark:text-slate-200">
              {positive ? '+' : ''}
              {value.toFixed(4)}
            </span>
          </li>
        );
      })}
    </ul>
  );
};
