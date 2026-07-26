import React from 'react'

interface LogoMarkProps {
  className?: string
}

export function LogoMark({ className = 'size-8' }: LogoMarkProps) {
  return (
    <svg
      className={className}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="FiduciaPay Logo"
    >
      <path
        d="M16 2L2 9V23L16 30L30 23V9L16 2Z"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinejoin="round"
      />
      <path
        d="M16 8V24"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
      <path
        d="M9 12L23 20"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
    </svg>
  )
}