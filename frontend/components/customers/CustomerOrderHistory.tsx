// ============================================================
// components/customers/CustomerOrderHistory.tsx
// ============================================================

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { CustomerOrdersResponse } from "@/types/contracts/customers";
import { EmptyState } from "@/components/shared/EmptyState";
import { ShoppingCart } from "lucide-react";
import Link from "next/link";

export function CustomerOrderHistory({ data }: { data: CustomerOrdersResponse }) {
  if (data.orders.length === 0) {
    return (
      <div className="border rounded-md py-12 bg-card">
        <EmptyState 
          title="No purchase history" 
          description="This customer hasn't placed any orders yet." 
          icon={ShoppingCart}
        />
      </div>
    );
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (isoString: string) => {
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
    }).format(new Date(isoString));
  };

  return (
    <div className="rounded-md border overflow-hidden bg-card">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Date</TableHead>
            <TableHead>Product</TableHead>
            <TableHead>Category</TableHead>
            <TableHead className="text-right">Qty</TableHead>
            <TableHead className="text-right">Price Paid</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.orders.map((order) => (
            <TableRow key={order.id}>
              <TableCell className="whitespace-nowrap">
                {formatDate(order.purchased_at)}
              </TableCell>
              <TableCell className="font-medium max-w-[200px] truncate">
                {order.product_name ? (
                  <Link href={`/products/${order.product_id}`} className="hover:underline">
                    {order.product_name}
                  </Link>
                ) : (
                  <span className="text-muted-foreground">{order.product_id} (Deleted)</span>
                )}
              </TableCell>
              <TableCell>{order.product_category || "—"}</TableCell>
              <TableCell className="text-right">{order.quantity}</TableCell>
              <TableCell className="text-right">{formatCurrency(order.price_paid)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
