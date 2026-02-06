"""
Intelligent Query Expander

Uses LLM to understand user intent and expand queries.

PROBLEM: User types "asteroid prediction" → 0 results
SOLUTION: LLM expands to ["asteroid", "near earth object", "space", "celestial"]
"""

import asyncio
import httpx
import logging
from typing import List
from src.config import settings

logger = logging.getLogger(__name__)

class QueryExpander:
    """
    Use LLM to expand user queries for better search results.
    
    Examples:
    - "asteroid prediction" → ["asteroid", "near earth object", "space"]
    - "diabetis" → ["diabetes", "blood sugar", "glucose"]
    - "cancer" → ["cancer", "tumor", "oncology", "malignant"]
    """
    
    def __init__(self, use_local_llm: bool = None):
        """
        Args:
            use_local_llm: If None, uses config default. Otherwise overrides config.
        """
        self.use_local_llm = use_local_llm if use_local_llm is not None else settings.USE_LOCAL_LLM
        self.lm_studio_url = settings.LLM_ENDPOINT
    
    async def expand_query(self, query: str) -> List[str]:
        """
        Expand a user query into multiple search terms.
        
        Args:
            query: User query (e.g., "cancer")
            
        Returns:
            List of expanded queries (e.g., ["cancer", "tumor", "oncology"])
        """
        if not self.use_local_llm:
            # Fallback: Return original query only
            logger.info("LLM disabled, returning original query")
            return [query]
        
        try:
            expanded = await self._call_llm(query)
            if expanded and len(expanded) > 0:
                logger.info(f"Expanded '{query}' to {len(expanded)} terms")
                return expanded
            else:
                return [query]
        except Exception as e:
            logger.warning(f"Query expansion failed: {e}")
            return [query]
    
    async def _call_llm(self, query: str) -> List[str]:
        """Call LM Studio to expand query"""
        prompt = f"""You are a dataset search assistant. Expand this query into 3-5 related search terms.

User query: "{query}"

Requirements:
- Include the original query
- Add synonyms, related terms, domain-specific keywords
- Keep terms concise (1-3 words each)
- Output ONLY a Python list, no explanations

Example:
Input: "cancer"
Output: ["cancer", "tumor", "oncology", "malignant"]

Now expand: "{query}"
Output:"""

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.lm_studio_url,
                    json={
                        "model": settings.LLM_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": settings.LLM_TEMP_QUERY_EXPANSION,
                        "max_tokens": settings.LLM_MAX_TOKENS
                    },
                    timeout=settings.LLM_TIMEOUT
                )
                response.raise_for_status()
                
                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()
                
                # Parse list from response
                import ast
                try:
                    # Try to parse as Python list
                    result = ast.literal_eval(content)
                    if isinstance(result, list):
                        return [str(item) for item in result]
                except:
                    pass
                
                # Fallback: split by commas
                return [term.strip().strip('"').strip("'") for term in content.split(",")]
                
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                return []


# Test function
async def test_query_expansion():
    """Test the query expander"""
    expander = QueryExpander(use_local_llm=True)
    
    test_queries = [
        "cancer",
        "asteroid prediction",
        "customer churn"
    ]
    
    print("\n" + "="*60)
    print("Query Expansion Test")
    print("="*60 + "\n")
    
    for query in test_queries:
        expanded = await expander.expand_query(query)
        print(f"Input:  '{query}'")
        print(f"Output: {expanded}")
        print()


if __name__ == "__main__":
    asyncio.run(test_query_expansion())
