import { cn } from '../lib/cn';

export function Input({
  label,
  error,
  className,
  id,
  type = 'text',
  ...props
}) {
  const inputId = id || label?.replace(/\s+/g, '-').toLowerCase();

  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label
          htmlFor={inputId}
          className="text-sm font-medium text-gray-300"
        >
          {label}
        </label>
      )}
      <input
        id={inputId}
        type={type}
        className={cn(
          'w-full rounded-lg border bg-slate-900/80 px-4 py-2.5 text-sm text-gray-100',
          'placeholder:text-gray-500',
          'transition-all duration-200',
          'focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-offset-gray-950',
          error
            ? 'border-red-500/60 focus:ring-red-500/40 focus:border-red-500/80'
            : 'border-slate-600/50 focus:ring-amber-500/40 focus:border-amber-500/60 hover:border-slate-500/60',
          className
        )}
        {...props}
      />
      {error && (
        <p className="text-xs text-red-400 mt-0.5">{error}</p>
      )}
    </div>
  );
}
