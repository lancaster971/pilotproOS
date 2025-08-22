import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "../../lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg font-medium transition-all duration-300 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2 focus-visible:ring-offset-focus-ring-offset disabled:pointer-events-none disabled:opacity-50 disabled:cursor-not-allowed [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        // Core variants - clean and professional
        default: "bg-primary text-primary-foreground hover:bg-primary/90 hover:scale-[1.02] active:scale-[0.98]",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90 hover:scale-[1.02] active:scale-[0.98]",
        outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground hover:border-brand-primary/30 hover:scale-[1.02] active:scale-[0.98]",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80 hover:scale-[1.02] active:scale-[0.98]",
        ghost: "hover:bg-accent hover:text-accent-foreground hover:scale-[1.02] active:scale-[0.98]",
        link: "text-primary underline-offset-4 hover:underline hover:text-brand-primary transition-colors",
        
        // Professional variants
        hero: "bg-gradient-primary text-brand-primary-foreground hover:scale-105 active:scale-[0.98] before:absolute before:inset-0 before:bg-gradient-to-r before:from-transparent before:via-white/20 before:to-transparent before:translate-x-[-100%] hover:before:translate-x-[100%] before:transition-transform before:duration-700",
        
        accent: "bg-gradient-accent text-brand-primary-foreground hover:scale-105 active:scale-[0.98] before:absolute before:inset-0 before:bg-gradient-to-r before:from-transparent before:via-white/20 before:to-transparent before:translate-x-[-100%] hover:before:translate-x-[100%] before:transition-transform before:duration-700",
        
        "outline-premium": "border-2 border-brand-primary/50 bg-transparent text-brand-primary hover:bg-brand-primary hover:text-brand-primary-foreground hover:border-brand-primary hover:scale-105 active:scale-[0.98] transition-all duration-300",
        
        "glass": "bg-white border border-gray-200 text-text-primary hover:bg-gray-50 hover:border-brand-primary/30 hover:scale-[1.02] active:scale-[0.98]",
        
        "glass-dark": "bg-black border border-gray-800 text-text-on-dark hover:bg-gray-900 hover:border-brand-primary/40 hover:scale-[1.02] active:scale-[0.98]",
        
        "outline-dark": "border border-white/50 bg-transparent text-white hover:bg-white/10 hover:border-white/80 hover:scale-[1.02] active:scale-[0.98]",

        "floating": "bg-gradient-primary text-brand-primary-foreground border border-brand-primary/20 hover:scale-105 active:scale-[0.98] hover:-translate-y-1 transition-all duration-300",
      },
      size: {
        xs: "h-8 px-3 py-1.5 text-xs rounded-md",
        sm: "h-9 px-4 py-2 text-sm rounded-md",
        default: "h-10 px-6 py-2.5 text-sm rounded-lg",
        lg: "h-12 px-8 py-3 text-base rounded-xl",
        xl: "h-14 px-10 py-4 text-lg rounded-xl",
        icon: "h-10 w-10 rounded-lg",
        "icon-sm": "h-8 w-8 rounded-md",
        "icon-lg": "h-12 w-12 rounded-xl",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }