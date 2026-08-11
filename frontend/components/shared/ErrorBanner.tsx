// ============================================================
// components/shared/ErrorBanner.tsx
//
// Inline error display with optional retry button.
// Used per-section (not full-page) for isolated error handling.
// ============================================================

import { AlertCircle, RefreshCcw } from "lucide-react";

interface ErrorBannerProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorBanner({ message, onRetry }: ErrorBannerProps) {
  return (
    <div
      role="alert"
      className="flex items-start gap-3 rounded-lg border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive"
    >
      <AlertCircle
        className="h-4 w-4 mt-0.5 shrink-0"
        aria-hidden="true"
      />
      <span className="flex-1">{message}</span>
      {onRetry && (
        <button
          onClick={onRetry}
          className="flex items-center gap-1 text-xs font-medium underline-offset-2 hover:underline shrink-0 transition-colors"
          aria-label="Retry"
        >
          <RefreshCcw className="h-3 w-3" aria-hidden="true" />
          Retry
        </button>
      )}
    </div>
  );
}
