interface Props {
  page: number;
  pages: number;
  onChange: (page: number) => void;
}

function getPageItems(page: number, pages: number): (number | "…")[] {
  if (pages <= 7) {
    return Array.from({ length: pages }, (_, i) => i + 1);
  }

  const visible = new Set<number>([1, pages]);
  for (let p = Math.max(2, page - 2); p <= Math.min(pages - 1, page + 2); p++) {
    visible.add(p);
  }

  const sorted = Array.from(visible).sort((a, b) => a - b);
  const items: (number | "…")[] = [];
  let previous = 0;

  for (const p of sorted) {
    if (p - previous > 1) items.push("…");
    items.push(p);
    previous = p;
  }

  return items;
}

export default function Pagination({ page, pages, onChange }: Props) {
  if (pages <= 1) return null;

  const items = getPageItems(page, pages);

  return (
    <nav
      aria-label="Pagination"
      className="mt-6 flex flex-wrap items-center justify-center gap-2"
    >
      <button
        disabled={page === 1}
        onClick={() => onChange(page - 1)}
        className="rounded-lg border border-slate-700/70 bg-slate-900/70 px-4 py-2 font-display text-sm font-semibold tracking-wide transition hover:border-cyan-500/50 hover:text-cyan-200 disabled:opacity-40 disabled:hover:border-slate-700/70 disabled:hover:text-slate-100"
      >
        Previous
      </button>

      {items.map((item, index) =>
        item === "…" ? (
          <span
            key={`ellipsis-${index}`}
            aria-hidden="true"
            className="px-1 text-slate-500"
          >
            …
          </span>
        ) : (
          <button
            key={item}
            onClick={() => onChange(item)}
            aria-label={`Page ${item}`}
            aria-current={item === page ? "page" : undefined}
            className={`h-10 w-10 rounded-lg font-display text-sm font-semibold tracking-wide transition ${
              item === page
                ? "bg-cyan-500 text-slate-950 shadow-glow"
                : "border border-slate-700/70 bg-slate-900/70 text-slate-300 hover:border-cyan-500/50 hover:text-cyan-200"
            }`}
          >
            {item}
          </button>
        )
      )}

      <button
        disabled={page === pages}
        onClick={() => onChange(page + 1)}
        className="rounded-lg border border-slate-700/70 bg-slate-900/70 px-4 py-2 font-display text-sm font-semibold tracking-wide transition hover:border-cyan-500/50 hover:text-cyan-200 disabled:opacity-40 disabled:hover:border-slate-700/70 disabled:hover:text-slate-100"
      >
        Next
      </button>
    </nav>
  );
}
