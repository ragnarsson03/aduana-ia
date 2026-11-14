import React from 'react';

interface ProgressBarProps {
  percentage: number;
  isPositive?: boolean;
  heightClass?: string;
  fillColor?: string;
  className?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  percentage,
  isPositive = true,
  heightClass = 'h-2.5',
  fillColor,
  className = '',
}) => {
  const defaultFill = isPositive
    ? 'bg-[#4f46e5] dark:bg-indigo-500'
    : 'bg-slate-400 dark:bg-slate-600';

  const color = fillColor || defaultFill;
  const width = Math.min(100, Math.max(0, percentage));

  return (
    <div className={`w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden ${heightClass} ${!isPositive ? 'flex justify-end' : ''} ${className}`}>
      <div
        className={`${color} rounded-full transition-all duration-500 ease-out`}
        style={{ width: `${width}%`, height: '100%' }}
      />
    </div>
  );
};
