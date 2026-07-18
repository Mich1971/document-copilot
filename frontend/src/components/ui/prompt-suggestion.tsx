import * as React from "react"
import { Button } from "@/components/ui/button"

export interface PromptSuggestionProps extends React.ComponentProps<typeof Button> {}

export function PromptSuggestion({ children, ...props }: PromptSuggestionProps) {
  return (
    <Button {...props}>
      {children}
    </Button>
  )
}
