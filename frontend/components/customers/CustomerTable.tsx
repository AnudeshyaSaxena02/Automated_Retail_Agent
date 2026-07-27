// ============================================================
// components/customers/CustomerTable.tsx
//
// Client-side paginated and filtered table for the Customer List.
// Maps rows to Customer 360 view.
// ============================================================

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { Customer } from "@/types/contracts/customers";
import { ChevronRight } from "lucide-react";
import { useRouter } from "next/navigation";
import { EmptyState } from "@/components/shared/EmptyState";

interface CustomerTableProps {
  customers: Customer[];
  emptyTitle?: string;
  emptyDescription?: string;
}

export function CustomerTable({ 
  customers, 
  emptyTitle = "No customers found",
  emptyDescription = "There are no customers matching the criteria."
}: CustomerTableProps) {
  const router = useRouter();

  if (customers.length === 0) {
    return (
      <div className="border rounded-md py-12">
        <EmptyState title={emptyTitle} description={emptyDescription} />
      </div>
    );
  }

  const formatDate = (isoString: string) => {
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    }).format(new Date(isoString));
  };

  return (
    <div className="rounded-md border overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Customer ID</TableHead>
            <TableHead>Name</TableHead>
            <TableHead>Email</TableHead>
            <TableHead>Joined</TableHead>
            <TableHead className="w-[50px]"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {customers.map((customer) => (
            <TableRow 
              key={customer.customer_id} 
              className="group cursor-pointer hover:bg-muted/50 transition-colors"
              onClick={() => router.push(`/customers/${customer.customer_id}`)}
            >
              <TableCell className="font-medium">
                {customer.customer_id}
              </TableCell>
              <TableCell>{customer.name}</TableCell>
              <TableCell>{customer.email || "—"}</TableCell>
              <TableCell>
                {formatDate(customer.created_at)}
              </TableCell>
              <TableCell>
                <ChevronRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
