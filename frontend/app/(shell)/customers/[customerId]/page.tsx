// ============================================================
// app/(shell)/customers/[customerId]/page.tsx
//
// Phase 4: Customer 360 View.
// Simultaneously fetches Profile, Memory, and Orders.
// ============================================================

"use client";

import { use } from "react";
import { useRouter } from "next/navigation";
import { PageHeader } from "@/components/shared/PageHeader";
import { useCustomer } from "@/hooks/useCustomer";
import { useCustomerMemory } from "@/hooks/useCustomerMemory";
import { useCustomerOrders } from "@/hooks/useCustomerOrders";
import { CustomerProfileCard } from "@/components/customers/CustomerProfileCard";
import { CustomerMemoryStats } from "@/components/customers/CustomerMemoryStats";
import { CustomerPreferences } from "@/components/customers/CustomerPreferences";
import { CustomerOrderHistory } from "@/components/customers/CustomerOrderHistory";
import { LoadingSkeleton } from "@/components/shared/LoadingSkeleton";
import { ErrorBanner } from "@/components/shared/ErrorBanner";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Inbox, BrainCircuit } from "lucide-react";
import { AxiosError } from "axios";
import { EmptyState } from "@/components/shared/EmptyState";

interface PageProps {
  params: Promise<{ customerId: string }>;
}

export default function Customer360Page({ params }: PageProps) {
  const router = useRouter();
  // Unwrap the Next.js 15+ promise-based params
  const { customerId } = use(params);

  // Parallel queries
  const { 
    data: profile, 
    isLoading: profileLoading, 
    error: profileError, 
    refetch: refetchProfile 
  } = useCustomer(customerId);

  const { 
    data: memory, 
    isLoading: memoryLoading, 
    error: memoryError, 
    refetch: refetchMemory 
  } = useCustomerMemory(customerId);

  const { 
    data: orders, 
    isLoading: ordersLoading, 
    error: ordersError, 
    refetch: refetchOrders 
  } = useCustomerOrders(customerId);

  // Helper to distinguish 404s (empty data) from actual failures (500, network, etc)
  const is404 = (err: Error | null) => {
    if (!err) return false;
    if ((err as AxiosError).response?.status === 404) return true;
    if (err.message.includes("404")) return true;
    return false;
  };

  // 1. Profile is the REQUIRED query. If it fails, the page fails.
  if (profileLoading) {
    return (
      <div className="space-y-6">
        <PageHeader title="Customer 360" description="Loading profile..." />
        <LoadingSkeleton variant="kpi" />
      </div>
    );
  }

  if (profileError) {
    return (
      <div className="space-y-6">
        <PageHeader 
          title="Customer 360" 
          description="Customer Profile" 
          actions={
            <Button variant="outline" onClick={() => router.push("/customers")}>
              <ArrowLeft className="mr-2 h-4 w-4" /> Back to Customers
            </Button>
          }
        />
        {is404(profileError) ? (
          <EmptyState 
            title="Customer Not Found" 
            description={`No customer found with ID "${customerId}".`}
            action={{ label: "View All Customers", onClick: () => router.push("/customers") }}
          />
        ) : (
          <ErrorBanner 
            message={profileError.message} 
            onRetry={() => refetchProfile()} 
          />
        )}
      </div>
    );
  }

  if (!profile) return null;

  const memoryIs404 = is404(memoryError);
  const ordersIs404 = is404(ordersError);

  return (
    <div className="space-y-8 pb-10">
      <PageHeader 
        title={`${profile.name} (360° View)`}
        description="Comprehensive view of the customer's profile, AI memory, and purchase history."
        actions={
          <Button variant="outline" onClick={() => router.push("/customers")}>
            <ArrowLeft className="mr-2 h-4 w-4" /> Back to Customers
          </Button>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column: Profile & Preferences */}
        <div className="space-y-8 lg:col-span-1">
          <CustomerProfileCard customer={profile} />

          {/* AI Memory & Preferences Section */}
          {memoryLoading ? (
            <LoadingSkeleton variant="card" />
          ) : memoryError && !memoryIs404 ? (
            <ErrorBanner 
              message={memoryError.message} 
              onRetry={() => refetchMemory()} 
            />
          ) : memoryIs404 ? (
            <div className="border rounded-md p-6 bg-card text-center">
              <BrainCircuit className="h-8 w-8 mx-auto text-muted-foreground mb-3 opacity-50" />
              <h3 className="font-semibold text-sm mb-1">No AI Memory Yet</h3>
              <p className="text-xs text-muted-foreground">Memory is generated after the first purchase.</p>
            </div>
          ) : memory ? (
            <CustomerPreferences memory={memory} />
          ) : null}
        </div>

        {/* Right Column: Stats & Order History */}
        <div className="space-y-8 lg:col-span-2">
          
          {/* Top Row: Memory Stats KPI Cards */}
          {memoryLoading ? (
            <LoadingSkeleton variant="kpi" />
          ) : memoryError && !memoryIs404 ? (
            <ErrorBanner 
              message={memoryError.message} 
              onRetry={() => refetchMemory()} 
            />
          ) : memory ? (
            <CustomerMemoryStats memory={memory} />
          ) : null}

          {/* Bottom Section: Order History Table */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold tracking-tight">Order History</h3>
            
            {ordersLoading ? (
              <LoadingSkeleton variant="list" />
            ) : ordersError && !ordersIs404 ? (
              <ErrorBanner 
                message={ordersError.message} 
                onRetry={() => refetchOrders()} 
              />
            ) : ordersIs404 ? (
              <div className="border rounded-md p-6 bg-card text-center">
                <Inbox className="h-8 w-8 mx-auto text-muted-foreground mb-3 opacity-50" />
                <h3 className="font-semibold text-sm mb-1">No Orders Found</h3>
                <p className="text-xs text-muted-foreground">This customer has no purchase history.</p>
              </div>
            ) : orders ? (
              <CustomerOrderHistory data={orders} />
            ) : null}
          </div>

        </div>
      </div>
    </div>
  );
}
