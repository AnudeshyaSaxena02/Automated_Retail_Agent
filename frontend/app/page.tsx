// ============================================================
// app/page.tsx
//
// Root page — redirects to /dashboard.
// Phase 1 infrastructure diagnostics have been preserved at /system.
// ============================================================

import { redirect } from "next/navigation";

export default function RootPage() {
  redirect("/dashboard");
}
