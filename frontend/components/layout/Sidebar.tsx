"use client";

// ============================================================
// components/layout/Sidebar.tsx
//
// Primary navigation sidebar.
// - Desktop: permanent, collapses to icon-only (CSS transition)
// - Mobile: rendered inside a Sheet drawer from AppLayout
//
// Navigation items:
//   Dashboard    /dashboard        — active
//   Products     /products         — active (stub Phase 3)
//   Customers    /customers        — active (stub Phase 4)
//   AI Workspace /ai               — active (stub Phase 5)
//   Orders       —                 — disabled, tooltip explains per-customer access
//   Knowledge    —                 — disabled, coming soon
//
// Sidebar state (collapsed/expanded) is owned by Zustand uiStore.
// Mobile open/close state is transient (passed as prop from AppLayout).
// ============================================================

import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Package,
  Users,
  Sparkles,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { Separator } from "@/components/ui/separator";
import { SidebarItem } from "@/components/layout/SidebarItem";
import { useUIStore } from "@/stores/uiStore";
import { cn } from "@/lib/utils";

interface NavItem {
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  href?: string;
  disabled?: boolean;
  tooltipContent?: string;
}

const NAV_ITEMS: NavItem[] = [
  {
    label: "Dashboard",
    icon: LayoutDashboard,
    href: "/dashboard",
  },
  {
    label: "Products",
    icon: Package,
    href: "/products",
  },
  {
    label: "Customers",
    icon: Users,
    href: "/customers",
  },
  {
    label: "AI Workspace",
    icon: Sparkles,
    href: "/ai",
  },
];

interface SidebarProps {
  /** When true, renders in compact (mobile-friendly) mode without the toggle button */
  compact?: boolean;
}

export function Sidebar({ compact = false }: SidebarProps) {
  const pathname = usePathname();
  const { sidebarCollapsed, toggleSidebar } = useUIStore();

  // In compact mode (inside Sheet drawer), never collapse
  const collapsed = compact ? false : sidebarCollapsed;

  return (
    <div
      className={cn(
        "flex flex-col h-full bg-background border-r border-border",
        "transition-[width] duration-200 ease-in-out",
        collapsed ? "w-16" : "w-60"
      )}
    >
      {/* Logo */}
      <div
        className={cn(
          "flex items-center gap-2 px-4 py-4 border-b border-border shrink-0",
          collapsed && "justify-center px-2"
        )}
      >
        <Sparkles
          className="h-5 w-5 text-primary shrink-0"
          aria-hidden="true"
        />
        {!collapsed && (
          <span className="font-semibold text-sm tracking-tight text-foreground">
            IDAM
          </span>
        )}
      </div>

      {/* Navigation */}
      <nav
        aria-label="Main navigation"
        className="flex-1 overflow-y-auto py-3 px-2 space-y-1"
      >
        {NAV_ITEMS.map((item) => {
          const active = item.href
            ? pathname === item.href || pathname.startsWith(item.href + "/")
            : false;
          return (
            <SidebarItem
              key={item.label}
              label={item.label}
              icon={item.icon as Parameters<typeof SidebarItem>[0]["icon"]}
              href={item.href}
              disabled={item.disabled}
              tooltipContent={item.tooltipContent}
              collapsed={collapsed}
              active={active}
            />
          );
        })}

        <Separator className="my-2" />

        {/* System link — visible only in expanded state */}
        {!collapsed && (
          <SidebarItem
            label="System"
            icon={LayoutDashboard}
            href="/system"
            collapsed={false}
            active={pathname === "/system"}
          />
        )}
      </nav>

      {/* Collapse toggle — desktop only */}
      {!compact && (
        <div className="shrink-0 border-t border-border px-2 py-2">
          <button
            onClick={toggleSidebar}
            className={cn(
              "flex items-center gap-2 w-full rounded-md px-3 py-2 text-sm text-muted-foreground",
              "hover:bg-accent hover:text-accent-foreground transition-colors",
              collapsed && "justify-center px-2"
            )}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4" aria-hidden="true" />
            ) : (
              <>
                <ChevronLeft className="h-4 w-4" aria-hidden="true" />
                <span>Collapse</span>
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
}
