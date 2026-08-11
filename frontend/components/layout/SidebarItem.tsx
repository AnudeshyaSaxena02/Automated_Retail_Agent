"use client";

// ============================================================
// components/layout/SidebarItem.tsx
//
// Individual navigation link in the sidebar.
// - Renders a Next.js Link when href is provided (active nav)
// - Renders a non-interactive span when disabled (no href)
// - Wraps with Tooltip: always when collapsed, always when disabled
// ============================================================

import Link from "next/link";
import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface SidebarItemProps {
  label: string;
  icon: LucideIcon;
  href?: string;
  disabled?: boolean;
  tooltipContent?: string;
  collapsed?: boolean;
  active?: boolean;
}

export function SidebarItem({
  label,
  icon: Icon,
  href,
  disabled = false,
  tooltipContent,
  collapsed = false,
  active = false,
}: SidebarItemProps) {
  const itemClass = cn(
    "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
    active
      ? "bg-primary/10 text-primary"
      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
    disabled && "opacity-50 cursor-not-allowed pointer-events-none",
    collapsed && "justify-center px-2"
  );

  const content = (
    <>
      <Icon
        className={cn("h-4 w-4 shrink-0", active && "text-primary")}
        aria-hidden="true"
      />
      {!collapsed && <span className="truncate">{label}</span>}
    </>
  );

  // Show tooltip when collapsed (shows label) or disabled (shows reason)
  const showTooltip = collapsed || disabled;
  const resolvedTooltip = tooltipContent ?? label;

  const element = disabled ? (
    <span
      className={itemClass}
      aria-disabled="true"
      role="menuitem"
      aria-label={label}
    >
      {content}
    </span>
  ) : (
    <Link
      href={href!}
      className={itemClass}
      aria-current={active ? "page" : undefined}
    >
      {content}
    </Link>
  );

  if (!showTooltip) return element;

  return (
    <Tooltip>
      <TooltipTrigger render={<span className="block" />}>
        {element}
      </TooltipTrigger>
      <TooltipContent side="right" sideOffset={8}>
        {resolvedTooltip}
      </TooltipContent>
    </Tooltip>
  );
}
