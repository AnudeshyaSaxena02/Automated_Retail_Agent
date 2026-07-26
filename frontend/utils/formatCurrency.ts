// ============================================================
// utils/formatCurrency.ts
//
// Formats numbers as Indian Rupees (INR) using Intl.NumberFormat.
// Pure function — no React, no side effects.
//
// Examples:
//   formatCurrency(12999)     → "₹12,999"
//   formatCurrency(89999.99)  → "₹89,999.99" (decimals shown only if non-zero)
//   formatCurrency(0)         → "₹0"
//   formatCurrency(null)      → "—"
//   formatCurrency(undefined) → "—"
// ============================================================

const INR_FORMATTER = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
});

export function formatCurrency(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return INR_FORMATTER.format(value);
}
