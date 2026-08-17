import { TrendingUp } from "lucide-react";
import Link from "next/link";

import { cn } from "@/lib/utils";

export function BrandMark({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground",
        className
      )}
    >
      <TrendingUp className="h-4 w-4" strokeWidth={2.5} />
    </span>
  );
}

export function Brand({
  href = "/",
  className,
}: {
  href?: string;
  className?: string;
}) {
  return (
    <Link
      href={href}
      className={cn("flex items-center gap-2 font-semibold", className)}
    >
      <BrandMark />
      <span className="text-base tracking-tight">Tradeork</span>
    </Link>
  );
}
