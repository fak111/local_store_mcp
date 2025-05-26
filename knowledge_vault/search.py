"""Knowledge search functionality with fuzzy matching."""

import re
from typing import Dict, List
from difflib import SequenceMatcher


class KnowledgeSearch:
    """Knowledge search engine with fuzzy text matching."""

    def __init__(self, storage):
        self.storage = storage

    def search(self, query: str, limit: int = 10, tag_filter: str = "") -> Dict:
        """Search knowledge records with fuzzy matching."""
        all_records = self.storage.get_all_records()

        # Filter by tags if specified
        if tag_filter:
            filter_tags = [tag.strip().lower() for tag in tag_filter.split(",")]
            filtered_records = []
            for record in all_records:
                record_tags = [tag.lower() for tag in record.get("tags", [])]
                if any(ftag in record_tags for ftag in filter_tags):
                    filtered_records.append(record)
            all_records = filtered_records

        # Score and rank records
        scored_results = []
        query_lower = query.lower()

        for record in all_records:
            score = self._calculate_score(record, query_lower)
            if score > 0:
                scored_results.append((score, record))

        # Sort by score (descending)
        scored_results.sort(key=lambda x: x[0], reverse=True)

        # Format results
        results = []
        for score, record in scored_results[:limit]:
            snippet = self._generate_snippet(record["content"], query_lower)
            results.append(
                {
                    "id": record["id"],
                    "title": record["title"],
                    "snippet": snippet,
                    "tags": record.get("tags", []),
                    "timestamp": record["timestamp"],
                    "score": score,
                }
            )

        return {"query": query, "total": len(scored_results), "results": results}

    def _calculate_score(self, record: Dict, query: str) -> float:
        """Calculate relevance score for a record."""
        title = record.get("title", "").lower()
        content = record.get("content", "").lower()
        tags = " ".join(record.get("tags", [])).lower()

        score = 0.0

        # Exact matches in title (highest weight)
        if query in title:
            score += 100

        # Exact matches in content
        if query in content:
            score += 50

        # Exact matches in tags
        if query in tags:
            score += 75

        # Fuzzy matching for partial matches
        title_similarity = SequenceMatcher(None, query, title).ratio()
        content_similarity = SequenceMatcher(None, query, content).ratio()

        score += title_similarity * 30
        score += content_similarity * 20

        # Boost for query word matches
        query_words = query.split()
        for word in query_words:
            if len(word) > 2:  # Skip very short words
                if word in title:
                    score += 10
                if word in content:
                    score += 5
                if word in tags:
                    score += 15

        return score

    def _generate_snippet(self, content: str, query: str, max_length: int = 150) -> str:
        """Generate a snippet highlighting the query context."""
        content_lower = content.lower()

        # Find the first occurrence of the query or query words
        best_pos = -1
        query_words = query.split()

        # Try exact query match first
        pos = content_lower.find(query)
        if pos != -1:
            best_pos = pos
        else:
            # Try individual words
            for word in query_words:
                if len(word) > 2:
                    pos = content_lower.find(word)
                    if pos != -1:
                        best_pos = pos
                        break

        if best_pos == -1:
            # No match found, return beginning
            snippet = content[:max_length]
        else:
            # Center the snippet around the match
            start = max(0, best_pos - max_length // 3)
            end = start + max_length
            snippet = content[start:end]

            # Add ellipsis if truncated
            if start > 0:
                snippet = "..." + snippet
            if end < len(content):
                snippet = snippet + "..."

        return snippet.strip()

    def search_recent(self, limit: int = 20) -> List[Dict]:
        """Get recent knowledge records."""
        records = self.storage.get_all_records()

        # Sort by timestamp (newest first)
        records.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        # Format results
        results = []
        for record in records[:limit]:
            snippet = record["content"][:150]
            if len(record["content"]) > 150:
                snippet += "..."

            results.append(
                {
                    "id": record["id"],
                    "title": record["title"],
                    "snippet": snippet,
                    "tags": record.get("tags", []),
                    "timestamp": record["timestamp"],
                }
            )

        return results
