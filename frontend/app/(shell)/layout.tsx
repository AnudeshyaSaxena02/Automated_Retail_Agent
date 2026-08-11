// ============================================================
// app/(shell)/layout.tsx
//
// Route group layout for all application shell pages.
// "(shell)" is invisible in the URL — it is a structural group only.
// No authentication. No route protection. All routes inside are open.
//
// Wraps children with AppLayout (sidebar + header).
// AppLayout is a Client Component; this layout is a Server Component.
// ============================================================

import { AppLayout } from "@/components/layout/AppLayout";

export default function ShellLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AppLayout>{children}</AppLayout>;
}
