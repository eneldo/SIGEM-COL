import { type InputHTMLAttributes, type ReactNode, forwardRef } from 'react'
import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  helperText?: string
  leftIcon?: ReactNode
  rightIcon?: ReactNode
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      helperText,
      leftIcon,
      rightIcon,
      className,
      id,
      ...props
    },
    ref,
  ) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-')

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-ink mb-1"
          >
            {label}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-ink-faint">
              {leftIcon}
            </div>
          )}
          <input
            ref={ref}
            id={inputId}
            className={twMerge(
              clsx(
                'block w-full rounded-lg border bg-paper-raised px-3 py-2 text-sm text-ink placeholder:text-ink-faint transition-colors',
                'focus:outline-none focus:ring-2 focus:ring-pine/30 focus:border-pine',
                error
                  ? 'border-warn focus:ring-warn/30 focus:border-warn'
                  : 'border-line',
                leftIcon && 'pl-10',
                rightIcon && 'pr-10',
                className,
              ),
            )}
            {...props}
          />
          {rightIcon && (
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center text-ink-faint">
              {rightIcon}
            </div>
          )}
        </div>
        {error && (
          <p className="mt-1 text-sm text-warn">{error}</p>
        )}
        {!error && helperText && (
          <p className="mt-1 text-sm text-ink-faint">{helperText}</p>
        )}
      </div>
    )
  },
)

Input.displayName = 'Input'
