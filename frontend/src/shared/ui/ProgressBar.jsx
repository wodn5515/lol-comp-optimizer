import { cn } from '../lib/cn';

export function ProgressBar({
  value = 0,
  max = 100,
  label,
  showPercent = true,
  className,
  barColor = 'bg-gradient-to-r from-amber-600 to-amber-400',
}) {
  const percent = Math.min(Math.round((value / max) * 100), 100);

  return (
    <div className={cn('w-full', className)}>
      {(label || showPercent) && (
        <div className="flex items-center justify-between mb-2">
          {label && (
            <span className="text-sm font-medium text-gray-300">{label}</span>
          )}
          {showPercent && (
            <span className="text-sm font-semibold text-amber-400">
              {percent}%
            </span>
          )}
        </div>
      )}
      <div className="h-2 w-full rounded-full bg-slate-800/80 overflow-hidden">
        <div
          className={cn(
            'h-full rounded-full transition-all duration-700 ease-out',
            barColor
          )}
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}
