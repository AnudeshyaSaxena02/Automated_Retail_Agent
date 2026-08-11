// ============================================================
// hooks/useCustomerOrders.ts
//
// TanStack Query hook for GET /customers/{customerId}/orders.
// ============================================================

import { useQuery } from "@tanstack/react-query";
import { getCustomerOrders } from "@/services/customerService";
import type { CustomerOrdersResponse } from "@/types/contracts/customers";

export function useCustomerOrders(customerId: string) {
  return useQuery<CustomerOrdersResponse, Error>({
    queryKey: ["customer-orders", customerId],
    queryFn: () => getCustomerOrders(customerId),
    staleTime: 60_000,
    gcTime: 5 * 60_000,
    retry: 1,
    refetchOnWindowFocus: false,
    enabled: !!customerId,
  });
}
