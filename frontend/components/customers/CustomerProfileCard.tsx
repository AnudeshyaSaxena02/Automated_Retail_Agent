// ============================================================
// components/customers/CustomerProfileCard.tsx
// ============================================================

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { User, Mail, Calendar, Hash } from "lucide-react";
import type { Customer } from "@/types/contracts/customers";

export function CustomerProfileCard({ customer }: { customer: Customer }) {
  const formatDate = (isoString: string) => {
    return new Intl.DateTimeFormat("en-US", {
      month: "long",
      day: "numeric",
      year: "numeric",
    }).format(new Date(isoString));
  };

  return (
    <Card>
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-2">
          <User className="h-5 w-5 text-primary" />
          Customer Profile
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-3">
          <Hash className="h-4 w-4 text-muted-foreground" />
          <div className="text-sm">
            <p className="text-muted-foreground font-medium text-xs">Customer ID</p>
            <p>{customer.customer_id}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <User className="h-4 w-4 text-muted-foreground" />
          <div className="text-sm">
            <p className="text-muted-foreground font-medium text-xs">Name</p>
            <p>{customer.name}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Mail className="h-4 w-4 text-muted-foreground" />
          <div className="text-sm">
            <p className="text-muted-foreground font-medium text-xs">Email</p>
            <p>{customer.email || "Not provided"}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Calendar className="h-4 w-4 text-muted-foreground" />
          <div className="text-sm">
            <p className="text-muted-foreground font-medium text-xs">Joined</p>
            <p>{formatDate(customer.created_at)}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
