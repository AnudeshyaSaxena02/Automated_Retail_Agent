// ============================================================
// hooks/useCustomer.ts
//
// TanStack Query hook for GET /customers/{customerId}.
// ============================================================

import { useQuery } from "@tanstack/react-query";
import { getCustomer } from "@/services/customerService";
import type { Customer } from "@/types/contracts/customers";

export function useCustomer(customerId: string) {
  return useQuery<Customer, Error>({
    queryKey: ["customer", customerId],
    queryFn: () => getCustomer(customerId),
    staleTime: 60_000,
    gcTime: 5 * 60_000,
    retry: 1,
    refetchOnWindowFocus: false,
    enabled: !!customerId,
  });
}
