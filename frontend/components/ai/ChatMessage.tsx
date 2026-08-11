"use client";

// ============================================================
// components/ai/ChatMessage.tsx
// ============================================================

import { ChatProductCard } from "./ChatProductCard";
import type { ChatProductItem } from "@/types/contracts/chat";
import { Sparkles, User, BadgeInfo } from "lucide-react";

// Safe markdown renderer for bold and simple lists
function renderInline(text: string) {
  const parts = text.split(/(\*\*.*?\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i} className="font-semibold text-foreground">
          {part.slice(2, -2)}
        </strong>
      );
    }
    // Handle inline newlines
    if (part.includes('\n')) {
       const subParts = part.split('\n');
       return (
         <span key={i}>
           {subParts.map((sp, j) => (
             <span key={j}>
               {sp}
               {j < subParts.length - 1 && <br />}
             </span>
           ))}
         </span>
       );
    }
    return <span key={i}>{part}</span>;
  });
}

function SafeMarkdown({ content }: { content: string }) {
  const paragraphs = content.split(/\n\n+/);

  return (
    <div className="space-y-3">
      {paragraphs.map((p, i) => {
        // Basic list detection
        if (p.trim().startsWith("- ") || p.trim().startsWith("* ")) {
          const items = p.split('\n').filter(line => line.trim().length > 0);
          return (
            <ul key={i} className="list-disc pl-5 space-y-1 my-2">
              {items.map((item, j) => (
                <li key={j}>{renderInline(item.replace(/^[-*]\s+/, ""))}</li>
              ))}
            </ul>
          );
        }
        return <p key={i}>{renderInline(p)}</p>;
      })}
    </div>
  );
}

export interface UiMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  intent?: string;
  products?: ChatProductItem[];
  metadata?: Record<string, unknown>;
}

export function ChatMessage({ message }: { message: UiMessage }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex w-full ${isUser ? "justify-end" : "justify-start"} mb-6`}>
      <div className={`flex max-w-[90%] md:max-w-[80%] ${isUser ? "flex-row-reverse" : "flex-row"} gap-3 min-w-0`}>
        {/* Avatar */}
        <div className={`flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center ${
          isUser ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground border border-border"
        }`}>
          {isUser ? <User className="h-4 w-4" /> : <Sparkles className="h-4 w-4" />}
        </div>

        {/* Message Content */}
        <div className="flex flex-col gap-1 min-w-0 flex-1">
          {/* Text Bubble */}
          <div className={`rounded-2xl px-5 py-4 text-sm break-words overflow-hidden ${
            isUser 
              ? "bg-primary text-primary-foreground rounded-tr-sm" 
              : "bg-muted/50 text-foreground border border-border rounded-tl-sm max-w-prose"
          }`}>
            <div className="leading-relaxed whitespace-normal">
              {isUser ? message.content : <SafeMarkdown content={message.content} />}
            </div>
          </div>
          
          {/* Intent / Metadata - Secondary visual weight below the text */}
          {!isUser && message.intent && (
            <div className="flex items-center gap-2 text-[10px] text-muted-foreground/60 px-1 mt-1">
              <span>Intent: {message.intent}</span>
              {Boolean(message.metadata?.rag_used) && (
                <span className="flex items-center gap-1">
                  &middot; <BadgeInfo className="h-3 w-3" /> Knowledge retrieved
                </span>
              )}
            </div>
          )}

          {/* Product Carousel (if products exist) */}
          {!isUser && message.products && message.products.length > 0 && (
            <div className="mt-4 w-full min-w-0">
              <p className="text-xs font-medium text-muted-foreground mb-3 px-1">
                Recommended {Math.min(message.products.length, 5)} product{Math.min(message.products.length, 5) !== 1 ? 's' : ''}
              </p>
              <div className="flex gap-4 overflow-x-auto pb-4 snap-x hide-scrollbar min-w-0 w-full" style={{ scrollbarWidth: 'none' }}>
                {message.products.slice(0, 5).map((p) => (
                  <div key={p.product_id} className="snap-start h-full shrink-0">
                    <ChatProductCard product={p} />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
