"use client";

// ============================================================
// components/layout/Breadcrumb.tsx
//
// Derives breadcrumb hierarchy from the current pathname.
// Uses shadcn Breadcrumb primitives.
// Last item is non-clickable (current page).
// ============================================================

import { usePathname } from "next/navigation";
import {
  Breadcrumb as BreadcrumbRoot,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";

// Static label mapping — no API calls required
const ROUTE_LABELS: Record<string, string> = {
  dashboard: "Dashboard",
  products: "Products",
  customers: "Customers",
  ai: "AI Workspace",
  system: "System",
  knowledge: "Knowledge Center",
  orders: "Orders",
};

function getLabel(segment: string): string {
  return ROUTE_LABELS[segment] ?? segment.charAt(0).toUpperCase() + segment.slice(1);
}

export function AppBreadcrumb() {
  const pathname = usePathname();

  // Split path into segments, filter empty strings
  const segments = pathname.split("/").filter(Boolean);

  if (segments.length === 0) return null;

  // Build cumulative hrefs: ["dashboard"] → "/dashboard", etc.
  const items = segments.map((segment, index) => ({
    label: getLabel(segment),
    href: "/" + segments.slice(0, index + 1).join("/"),
    isLast: index === segments.length - 1,
  }));

  return (
    <BreadcrumbRoot>
      <BreadcrumbList>
        {items.map((item, index) => (
          <span key={item.href} className="flex items-center gap-1.5">
            {index > 0 && <BreadcrumbSeparator />}
            <BreadcrumbItem>
              {item.isLast ? (
                <BreadcrumbPage>{item.label}</BreadcrumbPage>
              ) : (
                <BreadcrumbLink href={item.href}>{item.label}</BreadcrumbLink>
              )}
            </BreadcrumbItem>
          </span>
        ))}
      </BreadcrumbList>
    </BreadcrumbRoot>
  );
}
