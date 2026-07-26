// ============================================================
// app/(shell)/ai/page.tsx — Phase 5 stub
// ============================================================

import { PageHeader } from "@/components/shared/PageHeader";
import { Sparkles } from "lucide-react";

export const metadata = {
  title: "AI Workspace — IDAM",
};

export default function AiPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="AI Workspace"
        description="AI shopping assistant — coming in Phase 5"
      />
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <div className="rounded-full bg-muted p-6 mb-4">
          <Sparkles className="h-10 w-10 text-muted-foreground" aria-hidden="true" />
        </div>
        <h2 className="text-lg font-semibold text-foreground mb-2">
          AI Workspace — Phase 5
        </h2>
        <p className="text-sm text-muted-foreground max-w-sm">
          Conversational AI assistant, personalised recommendations, semantic
          search, and RAG-powered product queries will be implemented in Phase 5.
        </p>
      </div>
    </div>
  );
}
