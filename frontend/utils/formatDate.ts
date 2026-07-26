// ============================================================
// utils/formatDate.ts
//
// Formats ISO 8601 date strings to readable "15 Jan 2024" format.
// Pure function — no React, no side effects.
//
// Examples:
//   formatDate("2024-01-15T10:30:00Z") → "15 Jan 2024"
//   formatDate("2024-01-15")           → "15 Jan 2024"
//   formatDate(null)                   → "—"
//   formatDate(undefined)              → "—"
//   formatDate("")                     → "—"
// ============================================================

const DATE_FORMATTER = new Intl.DateTimeFormat("en-IN", {
  day: "2-digit",
  month: "short",
  year: "numeric",
});

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  try {
    const date = new Date(value);
    if (isNaN(date.getTime())) return "—";
    return DATE_FORMATTER.format(date);
  } catch {
    return "—";
  }
}
