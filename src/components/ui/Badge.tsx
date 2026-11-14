import React from 'react';

export type BadgeVariant = 'emerald' | 'amber' | 'rose' | 'indigo' | 'slate' | 'brand';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  hasDot?: boolean;
  pulseDot?: boolean;
  className?: string;
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'slate',
  hasDot = false,
  pulseDot = false,
  className = '',
  size = 'md',
}) => {
  const variantStyles: Record<BadgeVariant, { container: string; dot: string }> = {
    emerald: {
      container: 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400 border-emerald-200/80 dark:border-emerald-800/60',
      dot: 'bg-emerald-500',
    },
    amber: {
      container: 'bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-400 border-amber-200/80 dark:border-amber-800/60',
      dot: 'bg-amber-500',
    },
    rose: {
      container: 'bg-rose-50 dark:bg-rose-950/60 text-rose-700 dark:text-rose-400 border-rose-200/80 dark:border-rose-800/60',
      dot: 'bg-rose-500',
    },
    indigo: {
      container: 'bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-400 border-indigo-200/80 dark:border-indigo-800/60',
      dot: 'bg-indigo-500',
    },
    brand: {
      container: 'bg-[#4f46e5]/10 dark:bg-[#4f46e5]/20 text-[#4f46e5] dark:text-indigo-300 border-[#4f46e5]/30',
      dot: 'bg-[#4f46e5]',
    },
    slate: {
      container: 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700',
      dot: 'bg-slate-400',
    },
  };

  const sizeStyles = size === 'sm' 
    ? 'px-2 py-0.5 text-[10px]' 
    : 'px-2.5 py-0.5 text-xs';

  const current = variantStyles[variant];

  return (
    <span className={`inline-flex items-center gap-1.5 font-semibold rounded-full border shadow-2xs font-mono tracking-tight select-none ${sizeStyles} ${current.container} ${className}`}>
      {hasDot && (
        <span className={`w-1.5 h-1.5 rounded-full ${current.dot} ${pulseDot ? 'animate-pulse' : ''}`} />
      )}
      <span>{children}</span>
    </span>
  );
};
