import { cn } from '../lib/cn';

export function Card({ children, className, ...props }) {
  return (
    <div
      className={cn(
        'rounded-xl border border-gray-800 bg-gray-900',
        className
      )}
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
        'px-5 py-4 border-b border-gray-800',
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
