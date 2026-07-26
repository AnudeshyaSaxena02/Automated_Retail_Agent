// ============================================================
// services/customerService.ts
//
// Phase 2 scope: customer list and count for Dashboard.
// Full customer profile/memory/orders services added in Phase 4.
//
// Endpoint:
//   GET /customers → CustomerListResponse
// ============================================================

import { apiClient } from "@/lib/api-client";
import type { CustomerListResponse } from "@/types/contracts/customers";

export async function getCustomers(): Promise<CustomerListResponse> {
  const response = await apiClient.get<CustomerListResponse>("/customers");
  return response.data;
}
