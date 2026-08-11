"use client";

// ============================================================
// components/products/ProductToolbar.tsx
//
// Combines Search, Filters, and "Add Product" button.
// Manages the dual-mode logic: if search is active, filters are disabled.
// ============================================================

import { Search, X, Filter, Plus } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";

interface ProductToolbarProps {
  searchQuery: string;
  onSearchChange: (val: string) => void;
  category: string;
  onCategoryChange: (val: string) => void;
  brand: string;
  onBrandChange: (val: string) => void;
  minPrice: string;
  onMinPriceChange: (val: string) => void;
  maxPrice: string;
  onMaxPriceChange: (val: string) => void;
  onAddProductClick: () => void;
}

export function ProductToolbar({
  searchQuery,
  onSearchChange,
  category,
  onCategoryChange,
  brand,
  onBrandChange,
  minPrice,
  onMinPriceChange,
  maxPrice,
  onMaxPriceChange,
  onAddProductClick,
}: ProductToolbarProps) {
  const isSearchMode = searchQuery.trim().length > 0;

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row gap-4 justify-between items-start sm:items-center">
        {/* Search Bar */}
        <div className="relative w-full sm:max-w-md">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" aria-hidden="true" />
          <Input
            type="text"
            placeholder="Search products by name, category, brand..."
            className="pl-9 pr-9"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            aria-label="Search products"
          />
          {isSearchMode && (
            <button
              type="button"
              onClick={() => onSearchChange("")}
              className="absolute right-2.5 top-2.5 text-muted-foreground hover:text-foreground"
              aria-label="Clear search"
            >
              <X className="h-4 w-4" aria-hidden="true" />
            </button>
          )}
        </div>

        {/* Add Product Button */}
        <Button onClick={onAddProductClick} className="w-full sm:w-auto shrink-0">
          <Plus className="h-4 w-4 mr-2" aria-hidden="true" />
          Add Product
        </Button>
      </div>

      {/* Filters Area */}
      <div className="rounded-lg border border-border bg-card p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm font-medium text-foreground">
            <Filter className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
            Catalog Filters
          </div>
          {isSearchMode && (
            <span className="text-xs text-amber-600 dark:text-amber-400 font-medium">
              Clear search to use catalog filters.
            </span>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
          <div className="space-y-1.5">
            <Label htmlFor="category" className={isSearchMode ? "text-muted-foreground opacity-70" : ""}>
              Category
            </Label>
            <Input
              id="category"
              placeholder="e.g. Laptops"
              value={category}
              onChange={(e) => onCategoryChange(e.target.value)}
              disabled={isSearchMode}
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="brand" className={isSearchMode ? "text-muted-foreground opacity-70" : ""}>
              Brand
            </Label>
            <Input
              id="brand"
              placeholder="e.g. Dell"
              value={brand}
              onChange={(e) => onBrandChange(e.target.value)}
              disabled={isSearchMode}
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="min-price" className={isSearchMode ? "text-muted-foreground opacity-70" : ""}>
              Min Price (₹)
            </Label>
            <Input
              id="min-price"
              type="number"
              min="0"
              placeholder="0"
              value={minPrice}
              onChange={(e) => onMinPriceChange(e.target.value)}
              disabled={isSearchMode}
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="max-price" className={isSearchMode ? "text-muted-foreground opacity-70" : ""}>
              Max Price (₹)
            </Label>
            <Input
              id="max-price"
              type="number"
              min="0"
              placeholder="Any"
              value={maxPrice}
              onChange={(e) => onMaxPriceChange(e.target.value)}
              disabled={isSearchMode}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
