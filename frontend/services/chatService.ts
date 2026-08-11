import { apiClient } from "@/lib/api-client";
import type { ChatRequest, ChatResponse } from "@/types/contracts/chat";

export async function sendChatMessage(customerId: string, message: string): Promise<ChatResponse> {
  const request: ChatRequest = { message };
  const { data } = await apiClient.post<ChatResponse>(`/chat/${customerId}`, request);
  return data;
}
