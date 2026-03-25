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
          'w-full rounded-lg border bg-gray-900 px-4 py-2.5 text-sm text-gray-100',
          'placeholder:text-gray-500',
          'transition-colors',
          'focus:outline-none focus:ring-2 focus:ring-inset',
          error
            ? 'border-red-600 focus:ring-red-500/40'
            : 'border-gray-700 focus:ring-amber-500/40 focus:border-amber-600 hover:border-gray-600',
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
