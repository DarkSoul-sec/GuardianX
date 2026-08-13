import { Search } from "lucide-react";
import type { InputHTMLAttributes } from "react";

interface Props extends Omit<InputHTMLAttributes<HTMLInputElement>, "onChange"> {
  value: string;
  onChange: (v: string) => void;
  ariaLabel?: string;
}

export default function SearchInput({
  value,
  onChange,
  placeholder = "Search...",
  ariaLabel = "Search",
  className = "",
  ...props
}: Props) {
  return (
    <div className="relative w-full">
      <Search
        size={18}
        className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-cyan-400/60"
        aria-hidden="true"
      />
      <input
        {...props}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        aria-label={ariaLabel}
        className={`field pl-11 ${className}`}
      />
    </div>
  );
}
