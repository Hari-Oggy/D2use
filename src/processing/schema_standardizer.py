import asyncio
import json
from typing import Dict, List, Optional
import httpx
import logging

from ..config import settings

logger = logging.getLogger(__name__)

class SchemaStandardizer:
    """
    AI-powered schema standardizer using LM Studio.
    Cleans and standardizes column names in datasets.
    """
    
    def __init__(self, use_local_llm: bool = True):
        """
        Args:
            use_local_llm: If True, use LM Studio. If False, skip AI cleaning.
        """
        self.use_local_llm = use_local_llm
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.cache = {}  # Cache column mappings to reduce API calls
    
    async def standardize_columns(self, columns: List[str]) -> Dict[str, str]:
        """
        Standardize column names using AI.
        
        Args:
            columns: List of original column names
            
        Returns:
            Dict mapping original names to standardized names
        """
        # Check cache first
        cache_key = tuple(sorted(columns))
        if cache_key in self.cache:
            logger.info("Using cached column mapping")
            return self.cache[cache_key]
        
        if not self.use_local_llm:
            logger.warning("AI cleaning disabled, using simple standardization")
            return self._simple_standardize(columns)
        
        try:
            mapping = await self._standardize_with_llm(columns)
            
            if mapping:
                # Cache the result
                self.cache[cache_key] = mapping
                return mapping
            else:
                logger.warning("LLM standardization failed, using fallback")
                return self._simple_standardize(columns)
                
        except Exception as e:
            logger.error(f"Schema standardization error: {e}")
            return self._simple_standardize(columns)
    
    async def _standardize_with_llm(self, columns: List[str]) -> Optional[Dict[str, str]]:
        """Use LM Studio to standardize column names"""
        prompt = f"""You are a data cleaning expert. Standardize these dataset column names to snake_case format.

Rules:
1. Use lowercase with underscores (snake_case)
2. Remove special characters
3. Make names descriptive but concise
4. Common patterns:
   - "ID" → "id"
   - "Name" → "name"
   - "Date Created" → "created_date"
   - "User Name" → "user_name"
   - "Total Amount" → "total_amount"

Original columns:
{json.dumps(columns, indent=2)}

Return ONLY a JSON object mapping original names to standardized names:
{{
  "Original Name": "standardized_name",
  ...
}}

Return ONLY the JSON, no additional text."""
        
        payload = {
            "model": settings.LLM_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": settings.LLM_TEMP_SCHEMA_CLEANING,
            "max_tokens": settings.LLM_MAX_TOKENS
        }
        
        response = await self.http_client.post(settings.LLM_ENDPOINT, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        # Parse response
        if "choices" in data and len(data["choices"]) > 0:
            content = data["choices"][0]["message"]["content"].strip()
        else:
            raise ValueError(f"Unexpected LM Studio response format")
        
        # Extract JSON
        mapping = self._parse_json_response(content)
        
        # Validate mapping
        if mapping and all(col in mapping for col in columns):
            logger.info(f"✅ LLM standardized {len(columns)} columns")
            return mapping
        else:
            logger.warning("LLM response incomplete, using fallback")
            return None
    
    def _parse_json_response(self, content: str) -> Optional[Dict[str, str]]:
        """Parse JSON from LLM response"""
        try:
            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return None
    
    def _simple_standardize(self, columns: List[str]) -> Dict[str, str]:
        """Fallback: Simple rule-based standardization"""
        import re
        
        mapping = {}
        for col in columns:
            # Convert to lowercase
            standardized = col.lower()
            
            # Replace spaces and special chars with underscores
            standardized = re.sub(r'[^a-z0-9]+', '_', standardized)
            
            # Remove leading/trailing underscores
            standardized = standardized.strip('_')
            
            # Remove consecutive underscores
            standardized = re.sub(r'_+', '_', standardized)
            
            mapping[col] = standardized
        
        logger.info(f"Simple standardization: {len(columns)} columns")
        return mapping
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()


# Test function
async def test_schema_standardizer():
    """Test schema standardizer with messy column names"""
    standardizer = SchemaStandardizer(use_local_llm=True)
    
    # Test with messy column names (common in real datasets)
    messy_columns = [
        "User ID",
        "First Name",
        "Last Name",
        "Email Address",
        "Date of Birth",
        "Total Purchase Amount ($)",
        "Account Created Date",
        "Is Active?",
        "# of Orders"
    ]
    
    print(f"\n{'='*60}")
    print("Schema Standardizer Test (AI Column Cleaning)")
    print(f"{'='*60}\n")
    
    print("Original Columns:")
    for col in messy_columns:
        print(f"  - {col}")
    print()
    
    # Standardize
    print("Standardizing with LM Studio...\n")
    mapping = await standardizer.standardize_columns(messy_columns)
    
    print("Standardized Mapping:")
    for original, standardized in mapping.items():
        print(f"  '{original}' → '{standardized}'")
    print()
    
    # Verify quality
    all_snake_case = all('_' in v or v.islower() for v in mapping.values())
    no_special_chars = all(v.replace('_', '').isalnum() for v in mapping.values())
    
    print(f"{'='*60}")
    print("Quality Checks:")
    print(f"  ✅ All lowercase/snake_case: {all_snake_case}")
    print(f"  ✅ No special characters: {no_special_chars}")
    
    if all_snake_case and no_special_chars:
        print(f"\n✅ Schema standardization working correctly!")
    else:
        print(f"\n⚠️  Some columns need manual review")
    
    print(f"{'='*60}\n")
    
    await standardizer.close()


if __name__ == "__main__":
    asyncio.run(test_schema_standardizer())
