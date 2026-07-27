import { useMutation } from "@tanstack/react-query";
import { sendChatMessage } from "@/services/chatService";
import type { ChatResponse } from "@/types/contracts/chat";

export function useChat() {
  return useMutation<ChatResponse, Error, { customerId: string; message: string }>({
    mutationFn: ({ customerId, message }) => sendChatMessage(customerId, message),
  });
}
