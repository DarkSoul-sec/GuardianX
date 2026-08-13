import {
  cloneElement,
  isValidElement,
  type ButtonHTMLAttributes,
  type ReactElement,
  type ReactNode,
} from "react";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger";
  asChild?: boolean;
  children: ReactNode;
}

const variants: Record<NonNullable<Props["variant"]>, string> = {
  primary:
    "bg-cyan-500 text-slate-950 shadow-[0_0_20px_rgba(0,207,255,0.4)] hover:bg-cyan-400 hover:shadow-[0_0_28px_rgba(0,207,255,0.6)]",
  secondary:
    "border border-slate-700/70 bg-slate-900/70 text-slate-100 backdrop-blur-sm hover:border-cyan-500/50 hover:text-cyan-200",
  danger:
    "bg-red-600 text-white shadow-[0_0_20px_rgba(255,59,92,0.35)] hover:bg-red-500 hover:shadow-[0_0_28px_rgba(255,59,92,0.55)]",
};

export default function Button({
  children,
  variant = "primary",
  asChild = false,
  className = "",
  ...props
}: Props) {
  const classes = `inline-flex items-center justify-center rounded-lg px-5 py-2 font-display text-sm font-semibold tracking-wide transition disabled:cursor-not-allowed disabled:opacity-50 ${variants[variant]} ${className}`;

  if (asChild && isValidElement(children)) {
    const child = children as ReactElement<{ className?: string }>;
    return cloneElement(child, {
      className: `${classes} ${child.props.className ?? ""}`,
    });
  }

  return (
    <button {...props} className={classes}>
      {children}
    </button>
  );
}
