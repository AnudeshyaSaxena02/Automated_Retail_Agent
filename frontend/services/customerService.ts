// ============================================================
// services/customerService.ts
//
// Phase 2 scope: customer list and count for Dashboard.
// Phase 4 scope: profile, memory, and orders endpoints.
// ============================================================

import { apiClient } from "@/lib/api-client";
import type { 
  CustomerListResponse, 
  Customer, 
  CustomerMemory, 
  CustomerOrdersResponse 
} from "@/types/contracts/customers";

// ── Phase 2: Customer List ────────────────────────────────────
// Used by Dashboard and Customer Directory
export async function getCustomers(): Promise<CustomerListResponse> {
  const response = await apiClient.get<CustomerListResponse>("/customers");
  return response.data;
}

// ── Phase 4: Customer 360 ─────────────────────────────────────

export async function getCustomer(customerId: string): Promise<Customer> {
  const response = await apiClient.get<Customer>(`/customers/${customerId}`);
  return response.data;
}

export async function getCustomerMemory(customerId: string): Promise<CustomerMemory> {
  const response = await apiClient.get<CustomerMemory>(`/customers/${customerId}/memory`);
  return response.data;
}

export async function getCustomerOrders(customerId: string): Promise<CustomerOrdersResponse> {
  const response = await apiClient.get<CustomerOrdersResponse>(`/customers/${customerId}/orders`);
  return response.data;
}
