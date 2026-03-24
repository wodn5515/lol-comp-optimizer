import { cn } from '../lib/cn';

export function Card({ children, className, glowColor, ...props }) {
  return (
    <div
      className={cn(
        'relative rounded-xl border border-slate-700/50 bg-gradient-to-b from-slate-900/95 to-slate-950/95',
        'backdrop-blur-sm shadow-xl',
        'before:absolute before:inset-0 before:rounded-xl before:p-[1px]',
        'before:bg-gradient-to-b before:from-slate-600/20 before:to-transparent before:-z-10',
        className
      )}
      style={
        glowColor
          ? { boxShadow: `0 0 20px 0 ${glowColor}15, 0 0 40px 0 ${glowColor}08` }
          : undefined
      }
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children, className }) {
  return (
    <div
      className={cn(
        'px-5 py-4 border-b border-slate-700/40',
        className
      )}
    >
      {children}
    </div>
  );
}

export function CardContent({ children, className }) {
  return <div className={cn('px-5 py-4', className)}>{children}</div>;
}
