import React from 'react';
import { 
  Shield, 
  Lock, 
  Cpu, 
  LogOut, 
  Database,
  CheckCircle2 
} from 'lucide-react';
import { PipelineStageConfig } from '../../../types';

interface PipelineStageNodesProps {
  stages: PipelineStageConfig[];
  activeStageId?: string;
  onSelectStage?: (id: string) => void;
}

export const PipelineStageNodes: React.FC<PipelineStageNodesProps> = ({
  stages,
  activeStageId = 'ia-local',
  onSelectStage,
}) => {
  const renderIcon = (name: string, isActive: boolean) => {
    switch (name) {
      case 'shield':
        return <Shield className="w-5 h-5" />;
      case 'lock':
        return <Lock className="w-5 h-5" />;
      case 'cpu':
        return (
          <Cpu className={`w-5 h-5 ${isActive ? 'animate-spin' : ''}`} style={{ animationDuration: '10s' }} />
        );
      case 'log-out':
        return <LogOut className="w-5 h-5" />;
      case 'database':
        return <Database className="w-5 h-5" />;
      default:
        return <Shield className="w-5 h-5" />;
    }
  };

  return (
    <div className="grid grid-cols-5 gap-2 sm:gap-3 py-2 items-center">
      {stages.map((stage) => {
        const isActive = stage.id === activeStageId;
        const isCompleted = stage.status === 'completed';

        return (
          <button
            key={stage.id}
            onClick={() => onSelectStage?.(stage.id)}
            className={`group relative flex flex-col items-center text-center p-2.5 sm:p-3 rounded-xl transition-all cursor-pointer focus:outline-hidden ${
              isActive
                ? 'bg-white dark:bg-slate-800 border-2 border-[#4f46e5] dark:border-indigo-500 shadow-md transform -translate-y-1'
                : 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:border-[#4f46e5]/60 shadow-xs'
            }`}
          >
            {/* Active pulsating indicator */}
            {isActive && (
              <span className="absolute -top-1.5 right-1.5 flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500" />
              </span>
            )}

            {/* Icon Container */}
            <div 
              className={`w-9 h-9 sm:w-10 sm:h-10 rounded-xl flex items-center justify-center mb-1.5 sm:mb-2 shadow-2xs transition-colors ${
                isActive
                  ? 'bg-[#4f46e5] text-white'
                  : isCompleted
                  ? 'bg-indigo-50 dark:bg-indigo-950/60 text-[#4f46e5] dark:text-indigo-400'
                  : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300'
              }`}
            >
              {renderIcon(stage.iconName, isActive)}
            </div>

            {/* Title & Subtitle */}
            <h4 className={`font-bold text-xs leading-tight ${isActive ? 'text-[#4f46e5] dark:text-indigo-400' : 'text-slate-900 dark:text-white'}`}>
              {stage.name}
            </h4>
            <span className="text-[10px] text-slate-400 dark:text-slate-400 mt-0.5 truncate max-w-full">
              {stage.subtitle}
            </span>
          </button>
        );
      })}
    </div>
  );
};
