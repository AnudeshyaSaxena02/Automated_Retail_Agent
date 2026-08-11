import { useQuery } from "@tanstack/react-query";
import { getSemanticSearch } from "@/services/searchService";
import type { SemanticSearchResponse } from "@/types/contracts/search";

export function useSemanticSearch(query: string, limit: number = 10, minScore?: number, enabled: boolean = true) {
  return useQuery<SemanticSearchResponse, Error>({
    queryKey: ["semanticSearch", query, limit, minScore],
    queryFn: () => getSemanticSearch(query, limit, minScore),
    enabled: enabled && query.trim().length > 1,
  });
}
