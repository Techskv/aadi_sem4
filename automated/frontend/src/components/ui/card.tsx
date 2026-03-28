import * as React from "react"
import { cn } from "../../lib/utils"

export const Card = React.forwardRef<
    HTMLDivElement,
    React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
    <div
        ref={ref}
        className={cn(
            "rounded-xl border border-zinc-800 bg-zinc-900 text-white shadow-md relative overflow-hidden",
            className
        )}
        {...props}
    />
))
Card.displayName = "Card"
