import type { HTMLAttributes, ReactNode } from "react";

interface Props extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  className?: string;
}

export default function Card({
  children,
  className = "",
  ...props
}: Props) {
  return (
    <div {...props} className={`panel panel-hover p-6 ${className}`}>
      {children}
    </div>
  );
}
