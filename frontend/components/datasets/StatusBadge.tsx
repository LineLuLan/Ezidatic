import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium",
  {
    variants: {
      status: {
        pending: "border-transparent bg-muted text-muted-foreground",
        ready: "border-transparent bg-emerald-100 text-emerald-900 dark:bg-emerald-900/40 dark:text-emerald-200",
        failed: "border-transparent bg-destructive/10 text-destructive",
      },
    },
    defaultVariants: { status: "pending" },
  },
);

interface StatusBadgeProps extends VariantProps<typeof badgeVariants> {
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  return <span className={cn(badgeVariants({ status }), className)}>{status}</span>;
}
