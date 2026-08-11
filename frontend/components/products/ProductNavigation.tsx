"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

export function ProductNavigation() {
  const pathname = usePathname();

  const navItems = [
    {
      name: "Catalog",
      href: "/products",
      isActive: pathname === "/products",
    },
    {
      name: "Smart Search",
      href: "/products/search",
      isActive: pathname === "/products/search",
    },
  ];

  return (
    <nav className="flex space-x-4 border-b border-border mb-6" aria-label="Products">
      {navItems.map((item) => (
        <Link
          key={item.name}
          href={item.href}
          className={cn(
            "px-2 py-3 text-sm font-medium transition-colors hover:text-primary -mb-px",
            item.isActive
              ? "border-b-2 border-primary text-foreground"
              : "text-muted-foreground border-b-2 border-transparent hover:border-border"
          )}
          aria-current={item.isActive ? "page" : undefined}
        >
          {item.name}
        </Link>
      ))}
    </nav>
  );
}
