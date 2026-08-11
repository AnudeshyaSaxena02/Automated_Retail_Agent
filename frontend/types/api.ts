// ============================================================
// types/api.ts
//
// Genuinely shared API utilities and error types.
//
// These are not feature-specific. They describe the shape of
// HTTP error responses, pagination envelopes, and common
// response primitives that appear across multiple endpoints.
//
// Feature-specific contracts live in types/contracts/*.ts
// ============================================================

// ── HTTP / Axios error shapes ─────────────────────────────────

/**
 * The JSON body that FastAPI returns when it raises an HTTPException.
 * All backend error responses follow this shape.
 */
export interface BackendErrorDetail {
  /** Human-readable error message from the backend. */
  detail: string;
}

/**
 * Narrowly-typed representation of an Axios error whose response
 * body follows the FastAPI HTTPException convention.
 */
export interface ApiError {
  /** HTTP status code (e.g. 404, 422, 500). */
  status: number;
  /** The parsed `detail` field from the response body, if available. */
  message: string;
  /** The raw error object from Axios for advanced consumers. */
  raw: unknown;
}

/**
 * Extracts a human-readable message from an Axios or unknown error.
 * Use this in React Query `onError` callbacks or error boundaries.
 */
export function extractApiError(err: unknown): ApiError {
  // Axios errors carry a `response` property
  if (
    typeof err === "object" &&
    err !== null &&
    "response" in err &&
    typeof (err as { response?: unknown }).response === "object"
  ) {
    const resp = (err as { response: { status?: number; data?: unknown } })
      .response;
    const status = resp.status ?? 0;
    const detail =
      typeof resp.data === "object" &&
      resp.data !== null &&
      "detail" in resp.data
        ? String((resp.data as BackendErrorDetail).detail)
        : "Unknown error";
    return { status, message: detail, raw: err };
  }

  // Network errors (no response)
  if (
    typeof err === "object" &&
    err !== null &&
    "message" in err
  ) {
    return {
      status: 0,
      message: String((err as { message: string }).message),
      raw: err,
    };
  }

  return { status: 0, message: "Unknown error", raw: err };
}
