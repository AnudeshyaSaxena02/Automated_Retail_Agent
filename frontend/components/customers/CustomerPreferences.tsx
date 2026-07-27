// ============================================================
// components/customers/CustomerPreferences.tsx
// ============================================================

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tag, ShoppingBag, Heart } from "lucide-react";
import type { CustomerMemory } from "@/types/contracts/customers";

export function CustomerPreferences({ memory }: { memory: CustomerMemory }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">AI Memory & Preferences</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div>
          <h4 className="text-sm font-semibold flex items-center gap-2 mb-3">
            <Tag className="h-4 w-4 text-muted-foreground" />
            Purchased Categories
          </h4>
          <div className="flex flex-wrap gap-2">
            {memory.purchased_categories.length > 0 ? (
              memory.purchased_categories.map((cat) => (
                <Badge key={cat} variant="secondary">{cat}</Badge>
              ))
            ) : (
              <span className="text-sm text-muted-foreground">No category data</span>
            )}
          </div>
        </div>

        <div>
          <h4 className="text-sm font-semibold flex items-center gap-2 mb-3">
            <Heart className="h-4 w-4 text-muted-foreground" />
            Preferred Brands
          </h4>
          <div className="flex flex-wrap gap-2">
            {memory.preferred_brands.length > 0 ? (
              memory.preferred_brands.map((brand) => (
                <Badge key={brand} variant="outline">{brand}</Badge>
              ))
            ) : (
              <span className="text-sm text-muted-foreground">No brand data</span>
            )}
          </div>
        </div>

        <div>
          <h4 className="text-sm font-semibold flex items-center gap-2 mb-3">
            <ShoppingBag className="h-4 w-4 text-muted-foreground" />
            Category Interests (Observed)
          </h4>
          <div className="flex flex-wrap gap-2">
            {memory.category_interests.length > 0 ? (
              memory.category_interests.map((interest) => (
                <Badge key={interest} variant="default" className="bg-primary/10 text-primary hover:bg-primary/20 border-0">{interest}</Badge>
              ))
            ) : (
              <span className="text-sm text-muted-foreground">No interests recorded</span>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
