import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

/* ---------- surfaces ---------- */

export function Card({ className, children }: { className?: string; children: ReactNode }) {
  return (
    <div className={cn("rounded-[--radius-card] border bg-surface", className)}>{children}</div>
  );
}

export function SectionHeader({
  title,
  count,
  children,
}: {
  title: string;
  count?: number;
  children?: ReactNode;
}) {
  return (
    <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
      <h2 className="flex items-baseline gap-2 text-lg font-semibold">
        {title}
        {count !== undefined && (
          <span className="tabular text-sm font-normal text-ink-faint">{count}</span>
        )}
      </h2>
      {children}
    </div>
  );
}

/* ---------- controls ---------- */

type ButtonProps = {
  children: ReactNode;
  onClick?: () => void;
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md";
  disabled?: boolean;
  title?: string;
  className?: string;
};

export function Button({
  children,
  onClick,
  variant = "secondary",
  size = "md",
  disabled,
  title,
  className,
}: ButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      title={title}
      className={cn(
        "inline-flex shrink-0 items-center justify-center gap-1.5 rounded-md font-medium whitespace-nowrap",
        "transition-[transform,background-color,border-color] active:translate-y-px",
        "disabled:pointer-events-none disabled:opacity-45",
        size === "sm" ? "h-8 px-2.5 text-[13px]" : "h-9 px-3.5 text-sm",
        variant === "primary" && "bg-accent text-on-accent hover:opacity-90",
        variant === "secondary" && "border bg-surface text-ink hover:bg-sunken",
        variant === "ghost" && "text-ink-soft hover:bg-sunken hover:text-ink",
        className,
      )}
    >
      {children}
    </button>
  );
}

export function Pill({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "neutral" | "accent" | "good" | "attention" | "critical";
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium whitespace-nowrap",
        tone === "neutral" && "bg-sunken text-ink-soft",
        tone === "accent" && "bg-accent-soft text-accent-ink",
        tone === "good" && "bg-good-soft text-good",
        tone === "attention" && "bg-attention-soft text-attention",
        tone === "critical" && "bg-critical-soft text-critical",
      )}
    >
      {children}
    </span>
  );
}

/* ---------- the three states every list needs ---------- */

export function Loading({ rows = 3 }: { rows?: number }) {
  return (
    <div className="grid gap-2" aria-busy="true" aria-live="polite">
      <span className="sr-only">Loading</span>
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="h-[68px] animate-pulse rounded-[--radius-card] border bg-sunken"
          style={{ animationDelay: `${i * 90}ms` }}
        />
      ))}
    </div>
  );
}

export function Empty({
  title,
  hint,
  action,
  /** "Nothing overdue" is good news; it should not take up as much room as a
      section the user still has to go and fill. */
  quiet,
}: {
  title: string;
  hint?: string;
  action?: ReactNode;
  quiet?: boolean;
}) {
  if (quiet) {
    return (
      <Card className="flex flex-wrap items-baseline gap-x-2 gap-y-1 px-4 py-3">
        <p className="text-sm font-medium">{title}</p>
        {hint && <p className="text-sm text-ink-soft">{hint}</p>}
      </Card>
    );
  }

  return (
    <Card className="grid justify-items-center gap-3 px-6 py-10 text-center">
      <p className="font-medium">{title}</p>
      {hint && <p className="max-w-[46ch] text-sm text-ink-soft">{hint}</p>}
      {action}
    </Card>
  );
}

export function ErrorNote({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <Card className="flex flex-wrap items-center justify-between gap-3 border-critical/40 bg-critical-soft px-4 py-3">
      <p className="text-sm text-critical">{message}</p>
      {onRetry && (
        <Button size="sm" onClick={onRetry}>
          Try again
        </Button>
      )}
    </Card>
  );
}
