"use client";

// ============================================================
// components/ai/PromptInput.tsx
// ============================================================

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { SendHorizonal } from "lucide-react";
import { Input } from "@/components/ui/input";

interface PromptInputProps {
  onSend: (message: string) => void;
  isLoading: boolean;
  disabled?: boolean;
}

export function PromptInput({ onSend, isLoading, disabled }: PromptInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLInputElement>(null);

  // Auto-resize logic removed since Input doesn't resize, but keeping effect for safety if needed
  useEffect(() => {
  }, [value]);

  const handleSend = () => {
    if (!value.trim() || isLoading || disabled) return;
    onSend(value.trim());
    setValue("");
    
    // Reset height immediately after send
    // Removed height reset
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="relative flex items-end gap-2 bg-card border border-border rounded-xl p-2 shadow-sm focus-within:ring-1 focus-within:ring-primary focus-within:border-primary transition-all">
      <Input
        ref={textareaRef}
        value={value}
        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={disabled ? "Select a customer to start chatting..." : "Type your message..."}
        disabled={disabled || isLoading}
        className="bg-transparent border-0 focus-visible:ring-0 flex-grow shadow-none h-11"
      />
      <Button 
        size="icon" 
        className="h-11 w-11 shrink-0 rounded-lg mb-[1px]" 
        onClick={handleSend}
        disabled={!value.trim() || isLoading || disabled}
      >
        <SendHorizonal className="h-5 w-5" />
        <span className="sr-only">Send message</span>
      </Button>
    </div>
  );
}
