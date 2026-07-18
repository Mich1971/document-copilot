interface LogoMarkProps {
  className?: string
}

export function LogoMark({ className = 'size-8' }: LogoMarkProps) {
  return (
    <svg
      className={`${className} text-primary`}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <rect x="2" y="2" width="20" height="20" rx="5" stroke="currentColor" strokeWidth="2" />
      <path
        d="M7 17V7H10C12.5 7 14 8.5 14 11C14 13.5 12.5 15 10 15H9V17H7Z"
        fill="currentColor"
        className="text-primary/95"
      />
      <circle cx="16.5" cy="16.5" r="1.5" fill="currentColor" className="animate-pulse" />
    </svg>
  )
}
