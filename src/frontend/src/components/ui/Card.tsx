import { type ReactNode } from 'react'
import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

interface CardProps {
  children: ReactNode
  className?: string
}

interface CardSectionProps {
  children: ReactNode
  className?: string
}

export function Card({ children, className }: CardProps) {
  return (
    <div
      className={twMerge(
        clsx(
          'bg-paper-raised rounded-xl shadow-sm border border-line overflow-hidden',
          className,
        ),
      )}
    >
      {children}
    </div>
  )
}

export function CardHeader({ children, className }: CardSectionProps) {
  return (
    <div
      className={twMerge(
        clsx('px-6 py-4 border-b border-line', className),
      )}
    >
      {children}
    </div>
  )
}

export function CardContent({ children, className }: CardSectionProps) {
  return (
    <div className={twMerge(clsx('px-6 py-4', className))}>
      {children}
    </div>
  )
}

export function CardFooter({ children, className }: CardSectionProps) {
  return (
    <div
      className={twMerge(
        clsx('px-6 py-4 border-t border-line bg-paper/50', className),
      )}
    >
      {children}
    </div>
  )
}
