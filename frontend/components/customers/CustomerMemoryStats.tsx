// ============================================================
// components/customers/CustomerMemoryStats.tsx
// ============================================================

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Wallet, LineChart, Banknote, History } from "lucide-react";
import type { CustomerMemory } from "@/types/contracts/customers";

export function CustomerMemoryStats({ memory }: { memory: CustomerMemory }) {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(amount);
  };

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Spend</CardTitle>
          <Wallet className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{formatCurrency(memory.total_spend)}</div>
          <p className="text-xs text-muted-foreground mt-1">
            Across {memory.total_purchases} purchases
          </p>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Current Budget Est.</CardTitle>
          <LineChart className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {memory.current_budget_estimate !== null 
              ? formatCurrency(memory.current_budget_estimate) 
              : "—"}
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Based on monthly history
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Start of Month Avg</CardTitle>
          <Banknote className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{formatCurrency(memory.avg_budget_start)}</div>
          <p className="text-xs text-muted-foreground mt-1">Days 1–10</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">End of Month Avg</CardTitle>
          <History className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{formatCurrency(memory.avg_budget_end)}</div>
          <p className="text-xs text-muted-foreground mt-1">Days 21–31</p>
        </CardContent>
      </Card>
    </div>
  );
}
