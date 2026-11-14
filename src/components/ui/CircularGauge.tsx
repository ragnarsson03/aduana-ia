import React from 'react';

interface CircularGaugeProps {
  value: number; // 0 to 100
  size?: number; // width/height in px
  strokeWidth?: number;
  label?: string;
  sublabel?: string;
  color?: string; // Tailwind color class or hex
  trackColor?: string;
  className?: string;
}

export const CircularGauge: React.FC<CircularGaugeProps> = ({
  value,
  size = 64,
  strokeWidth = 3.5,
  label,
  sublabel,
  color = 'text-brand-600 dark:text-brand-500',
  trackColor = 'text-slate-200 dark:text-slate-700',
  className = '',
}) => {
  const normalizedValue = Math.min(100, Math.max(0, value));
  const radius = 15.9155; // standard viewBox 36x36 for circumference 100
  const dashArray = `${normalizedValue}, 100`;

  return (
    <div 
      className={`relative shrink-0 flex items-center justify-center ${className}`}
      style={{ width: `${size}px`, height: `${size}px` }}
    >
      <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
        {/* Track circle */}
        <path
          className={trackColor}
          d={`M18 2.0845 a ${radius} ${radius} 0 0 1 0 31.831 a ${radius} ${radius} 0 0 1 0 -31.831`}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
        />
        {/* Progress circle */}
        <path
          className={`${color} transition-all duration-700 ease-out`}
          d={`M18 2.0845 a ${radius} ${radius} 0 0 1 0 31.831 a ${radius} ${radius} 0 0 1 0 -31.831`}
          fill="none"
          stroke="currentColor"
          strokeDasharray={dashArray}
          strokeLinecap="round"
          strokeWidth={strokeWidth}
        />
      </svg>
      
      {/* Centered text */}
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center leading-none">
        {label ? (
          <span className="font-mono text-xs font-black text-slate-800 dark:text-slate-100">
            {label}
          </span>
        ) : (
          <span className="font-mono text-xs font-bold text-slate-800 dark:text-slate-100">
            {normalizedValue}%
          </span>
        )}
        {sublabel && (
          <span className="text-[8px] font-mono text-slate-400 mt-0.5">
            {sublabel}
          </span>
        )}
      </div>
    </div>
  );
};
