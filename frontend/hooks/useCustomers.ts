// ============================================================
// hooks/useCustomers.ts
//
// TanStack Query wrapper for GET /customers.
// Provides total count AND the full customer list.
// Used by Dashboard: total count (KPI) + Customer Overview section.
//
// Query key: ["customers"]
// Stale time: 60s
// ============================================================

import { useQuery } from "@tanstack/react-query";
import { getCustomers } from "@/services/customerService";
import type { CustomerListResponse } from "@/types/contracts/customers";

export function useCustomers() {
  return useQuery<CustomerListResponse, Error>({
    queryKey: ["customers"],
    queryFn: getCustomers,
    staleTime: 60_000,
    gcTime: 5 * 60_000,
    retry: 1,
    refetchOnWindowFocus: false,
  });
}
