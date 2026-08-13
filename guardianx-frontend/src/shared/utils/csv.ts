/**
 * Client-side CSV export utilities.
 */

export interface CsvColumn<T> {
  header: string;
  value: (row: T) => string | number | null | undefined;
}

const FORMULA_PREFIX = /^[=+\-@\t\r]/;

function escapeCell(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return "";
  const string = String(value);
  // Prevent CSV formula injection: cells beginning with =, +, -, @, tab or
  // CR are prefixed with a single quote so spreadsheets render them as text
  // instead of evaluating them as formulas.
  const sanitized = FORMULA_PREFIX.test(string) ? `'${string}` : string;
  if (/[",\n]/.test(sanitized)) {
    return `"${sanitized.replace(/"/g, '""')}"`;
  }
  return sanitized;
}

export function buildCsv<T>(columns: CsvColumn<T>[], rows: T[]): string {
  const header = columns.map((column) => escapeCell(column.header)).join(",");
  const body = rows.map((row) =>
    columns.map((column) => escapeCell(column.value(row))).join(",")
  );
  return [header, ...body].join("\n");
}

export function downloadCsv(filename: string, content: string): void {
  const blob = new Blob([content], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function exportRowsToCsv<T>(
  filename: string,
  columns: CsvColumn<T>[],
  rows: T[]
): void {
  downloadCsv(filename, buildCsv(columns, rows));
}
