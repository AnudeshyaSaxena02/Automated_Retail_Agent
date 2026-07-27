// ============================================================
// hooks/useCustomerMemory.ts
//
// TanStack Query hook for GET /customers/{customerId}/memory.
// ============================================================

import { useQuery } from "@tanstack/react-query";
import { getCustomerMemory } from "@/services/customerService";
import type { CustomerMemory } from "@/types/contracts/customers";

export function useCustomerMemory(customerId: string) {
  return useQuery<CustomerMemory, Error>({
    queryKey: ["customer-memory", customerId],
    queryFn: () => getCustomerMemory(customerId),
    staleTime: 60_000,
    gcTime: 5 * 60_000,
    retry: 1,
    refetchOnWindowFocus: false,
    enabled: !!customerId,
  });
}
