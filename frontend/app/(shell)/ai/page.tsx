"use client";

// ============================================================
// app/(shell)/ai/page.tsx
//
// AI Workspace (Phase 5).
// Powered by POST /chat/{customer_id}
//
// Maintains local state for the active customer and conversation.
// ============================================================

import { useState, useRef, useEffect } from "react";
import { PageHeader } from "@/components/shared/PageHeader";
import { useCustomers } from "@/hooks/useCustomers";
import { useChat } from "@/hooks/useChat";
import { ChatMessage, UiMessage } from "@/components/ai/ChatMessage";
import { PromptInput } from "@/components/ai/PromptInput";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Sparkles, Bot } from "lucide-react";
import { ErrorBanner } from "@/components/shared/ErrorBanner";

export default function AiWorkspacePage() {
  const [selectedCustomerId, setSelectedCustomerId] = useState<string>("");
  const [messages, setMessages] = useState<UiMessage[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);
  
  // Track active customer to prevent race conditions on late responses
  const activeCustomerRef = useRef<string>(selectedCustomerId);
  useEffect(() => {
    activeCustomerRef.current = selectedCustomerId;
  }, [selectedCustomerId]);

  // Fetch available customers for the context selector
  const { data: customersData, isLoading: isLoadingCustomers } = useCustomers();
  const customers = customersData?.customers || [];

  // Chat mutation
  const chatMutation = useChat();

  // Auto-scroll to bottom of the dedicated viewport
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: "smooth"
      });
    }
  }, [messages, chatMutation.isPending]);

  const handleSendMessage = (content: string) => {
    if (!selectedCustomerId || !content.trim()) return;

    // 1. Add user message to UI immediately
    const userMsg: UiMessage = {
      id: Date.now().toString(),
      role: "user",
      content,
    };
    setMessages((prev) => [...prev, userMsg]);

    // 2. Trigger mutation
    chatMutation.mutate(
      { customerId: selectedCustomerId, message: content },
      {
        onSuccess: (data, variables) => {
          // Ignore stale responses if the user switched customers while pending
          if (variables.customerId !== activeCustomerRef.current) return;

          // 3. Add AI response to UI
          const aiMsg: UiMessage = {
            id: Date.now().toString() + "-ai",
            role: "assistant",
            content: data.response,
            intent: data.intent,
            products: data.products,
            metadata: data.metadata,
          };
          setMessages((prev) => [...prev, aiMsg]);
        },
        onError: (_, variables) => {
          // Ignore stale responses
          if (variables.customerId !== activeCustomerRef.current) return;
          
          // Add error message to UI
          const errorMsg: UiMessage = {
            id: Date.now().toString() + "-error",
            role: "assistant",
            content: "Sorry, I encountered an error processing your request. Please try again.",
          };
          setMessages((prev) => [...prev, errorMsg]);
        }
      }
    );
  };

  const handleCustomerChange = (customerId: string | null) => {
    if (!customerId) return;
    setSelectedCustomerId(customerId);
    // Clear conversation when switching context
    setMessages([]);
    chatMutation.reset();
  };

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)] -m-4 md:-m-6 bg-background">
      {/* Scrollable Content Area (Header, Selector, Messages) */}
      <div ref={scrollRef} className="flex-1 min-h-0 overflow-y-auto">
        <div className="max-w-5xl mx-auto w-full p-4 md:p-6 flex flex-col min-h-full">
          <PageHeader
            title="AI Workspace"
            description="Your AI-powered shopping assistant. Select a customer context to begin."
          />

          {/* Customer Context Selector */}
          <div className="bg-card border border-border p-4 rounded-xl mt-6 flex items-center gap-4 shrink-0">
            <Label htmlFor="customer-select" className="shrink-0 font-medium text-muted-foreground flex items-center gap-2">
              <Bot className="h-4 w-4" />
              Customer Context:
            </Label>
            
            <div className="w-[300px]">
              <Select 
                value={selectedCustomerId} 
                onValueChange={handleCustomerChange}
                disabled={isLoadingCustomers}
              >
                <SelectTrigger id="customer-select" className="bg-background">
                  <SelectValue placeholder={isLoadingCustomers ? "Loading customers..." : "Select a customer..."}>
                    {selectedCustomerId && customers.find(c => c.customer_id === selectedCustomerId) 
                      ? `${customers.find(c => c.customer_id === selectedCustomerId)?.name} · ${selectedCustomerId}` 
                      : undefined}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {customers.map((c) => (
                    <SelectItem key={c.customer_id} value={c.customer_id}>
                      {c.name} &middot; {c.customer_id}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            {!selectedCustomerId && (
              <p className="text-sm text-muted-foreground ml-auto hidden md:block">
                Required for personalized history & recommendations
              </p>
            )}
          </div>

          {/* Main Chat Area */}
          <div className="flex-1 flex flex-col mt-4">
            {!selectedCustomerId ? (
              <div className="flex-1 flex flex-col items-center justify-center p-8 text-center animate-in fade-in">
                 <div className="rounded-full bg-muted p-6 mb-4">
                   <Sparkles className="h-10 w-10 text-muted-foreground opacity-50" />
                 </div>
                 <h3 className="text-lg font-medium text-foreground mb-2">Context Required</h3>
                 <p className="text-sm text-muted-foreground max-w-sm">
                   Please select a customer from the dropdown above to initialize the AI Assistant&apos;s memory and recommendation engine.
                 </p>
              </div>
            ) : (
              <div className="flex flex-col w-full h-full">
                {messages.length === 0 ? (
                  <div className="flex-1 flex flex-col items-center justify-center text-center p-4">
                     <Bot className="h-12 w-12 text-primary/20 mb-4" />
                     <h3 className="text-lg font-medium mb-2">Ready to assist {customers.find(c => c.customer_id === selectedCustomerId)?.name}</h3>
                     <p className="text-sm text-muted-foreground max-w-md">
                       Ask about order history, request recommendations, or perform semantic product searches.
                     </p>
                  </div>
                ) : (
                  <div className="w-full pb-4">
                    {messages.map((msg) => (
                      <ChatMessage key={msg.id} message={msg} />
                    ))}

                    {chatMutation.isPending && (
                      <div className="flex w-full justify-start mb-6">
                        <div className="flex max-w-[85%] flex-row gap-3">
                          <div className="flex-shrink-0 h-8 w-8 rounded-full bg-muted text-muted-foreground border border-border flex items-center justify-center">
                            <Sparkles className="h-4 w-4 animate-pulse" />
                          </div>
                          <div className="rounded-2xl px-4 py-3 text-sm bg-muted text-foreground border border-border rounded-tl-sm">
                            <div className="flex gap-1 items-center h-5">
                               <div className="w-1.5 h-1.5 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                               <div className="w-1.5 h-1.5 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                               <div className="w-1.5 h-1.5 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Input Area (Static at Bottom, Non-Shrinking) */}
      <div className="shrink-0 border-t border-border bg-background/95 backdrop-blur-md p-4 md:p-6 z-10">
        <div className="max-w-5xl mx-auto w-full">
          {chatMutation.isError && (
             <ErrorBanner
               message={chatMutation.error.message || "An error occurred while communicating with the AI."}
             />
          )}
          
          <PromptInput 
            onSend={handleSendMessage}
            isLoading={chatMutation.isPending}
            disabled={!selectedCustomerId}
          />
          <div className="text-center mt-2">
            <p className="text-[10px] text-muted-foreground">
              AI responses are generated based on the selected customer&apos;s profile, history, and real-time product catalog data.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
