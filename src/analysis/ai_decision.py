import asyncio
import json
from typing import Dict, Optional, List
import httpx
import logging
from pydantic import BaseModel, Field, validator
from src.config import settings

logger = logging.getLogger(__name__)

# LM Studio endpoint from config
LMSTUDIO_ENDPOINT = settings.LLM_ENDPOINT

class CleaningRecipe(BaseModel):
    """
    Validated cleaning recipe from AI.
    
    DESIGN DECISION: Use Pydantic for strict validation
    - Prevents AI hallucinations from breaking the pipeline
    - Ensures all fields are present and valid types
    """
    target_column: Optional[str] = Field(None, description="Column to use as ML target (for stratification)")
    outlier_strategy: str = Field("keep", description="How to handle outliers: 'clip', 'drop', or 'keep'")
    impute_strategy: str = Field("drop_rows", description="How to handle nulls: 'mean', 'median', 'mode', or 'drop_rows'")
    type_conversions: Dict[str, str] = Field(default_factory=dict, description="Column -> target type (e.g., {'age': 'Int64'})")
    drop_columns: List[str] = Field(default_factory=list, description="Columns to drop (e.g., high-cardinality IDs)")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="AI's confidence in this recipe (0-1)")
    reasoning: str = Field("", description="AI's explanation for its decisions")
    
    @validator('outlier_strategy')
    def validate_outlier_strategy(cls, v):
        valid = ['clip', 'drop', 'keep']
        if v not in valid:
            raise ValueError(f"outlier_strategy must be one of {valid}")
        return v
    
    @validator('impute_strategy')
    def validate_impute_strategy(cls, v):
        valid = ['mean', 'median', 'mode', 'drop_rows', 'keep']
        if v not in valid:
            raise ValueError(f"impute_strategy must be one of {valid}")
        return v


class AIDecisionMaker:
    """
    AI-powered decision maker for data cleaning strategies.
    
    DESIGN DECISIONS (Senior Engineer Review):
    1. Validation: Pydantic schema prevents invalid recipes
    2. Sanity Checks: Verify AI suggestions make sense (e.g., can't impute categorical with mean)
    3. Fallback: Conservative defaults if AI fails
    4. Context Limits: Truncate large profiles to fit in 8K token window
    """
    
    def __init__(self, use_local_llm: bool = True):
        self.use_local_llm = use_local_llm
        self.http_client = httpx.AsyncClient(timeout=60.0)
    
    async def get_cleaning_recipe(self, profile: Dict) -> CleaningRecipe:
        """
        Get AI-recommended cleaning recipe from dataset profile.
        
        Args:
            profile: Statistical profile from DatasetProfiler
            
        Returns:
            Validated CleaningRecipe
        """
        if not self.use_local_llm:
            logger.warning("AI disabled, using conservative defaults")
            return self._get_default_recipe(profile)
        
        try:
            recipe = await self._ask_llm(profile)
            
            if recipe:
                # Sanity check the recipe
                validated_recipe = self._validate_recipe(recipe, profile)
                return validated_recipe
            else:
                logger.warning("LLM failed, using defaults")
                return self._get_default_recipe(profile)
                
        except Exception as e:
            logger.error(f"AI decision error: {e}")
            return self._get_default_recipe(profile)
    
    async def _ask_llm(self, profile: Dict) -> Optional[CleaningRecipe]:
        """Ask LM Studio for cleaning recommendations"""
        # Truncate profile for context window
        truncated_profile = self._truncate_profile(profile)
        
        prompt = f"""You are a Senior Data Scientist. Analyze this dataset profile and recommend a cleaning strategy.

Dataset Profile:
{json.dumps(truncated_profile, indent=2)}

Your task:
1. Identify the TARGET COLUMN for machine learning (likely a low-cardinality categorical)
2. Recommend how to handle OUTLIERS (clip to bounds, drop rows, or keep)
3. Recommend how to handle MISSING VALUES (impute with mean/median/mode, or drop rows)
4. Suggest TYPE CONVERSIONS if needed (e.g., string "123" -> Int64)
5. Suggest columns to DROP (e.g., high-cardinality IDs, all-null columns)

Rules:
- For NUMERIC columns with outliers: Consider 'clip' if <20% outliers, 'keep' otherwise
- For MISSING values: Use 'drop_rows' if <5% missing, 'mean/median' if 5-30%, 'keep' if >30%
- For CATEGORICAL: Never use mean/median imputation
- TARGET COLUMN: Should be categorical with 2-50 unique values
- CONFIDENCE: Rate 0.0-1.0 based on data quality

Return ONLY valid JSON matching this schema:
{{
  "target_column": "column_name or null",
  "outlier_strategy": "clip|drop|keep",
  "impute_strategy": "mean|median|mode|drop_rows|keep",
  "type_conversions": {{"column": "Int64|Float64|Utf8|Date"}},
  "drop_columns": ["col1", "col2"],
  "confidence": 0.85,
  "reasoning": "Brief explanation of your decisions"
}}

Return ONLY the JSON, no markdown, no extra text."""

        payload = {
            "model": settings.LLM_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": settings.LLM_TEMP_AI_DECISION,
            "max_tokens": settings.LLM_MAX_TOKENS
        }
        
        try:
            response = await self.http_client.post(LMSTUDIO_ENDPOINT, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0]["message"]["content"].strip()
            else:
                raise ValueError("Unexpected LM Studio response format")
            
            # Parse JSON
            recipe_dict = self._parse_json_response(content)
            
            if recipe_dict:
                # Validate with Pydantic
                recipe = CleaningRecipe(**recipe_dict)
                logger.info(f"✅ AI recipe generated (confidence: {recipe.confidence:.2f})")
                return recipe
            else:
                return None
                
        except httpx.HTTPError as e:
            logger.error(f"LM Studio request failed: {e}")
            return None
    
    def _parse_json_response(self, content: str) -> Optional[Dict]:
        """Parse JSON from LLM response"""
        try:
            # Remove markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            return json.loads(content.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON: {e}")
            logger.debug(f"Raw content: {content[:500]}")
            return None
    
    def _truncate_profile(self, profile: Dict, max_columns: int = 20) -> Dict:
        """Truncate profile to fit context window"""
        truncated = {
            "dataset_info": profile.get("dataset_info", {}),
            "insights": profile.get("insights", {}),
            "columns": {}
        }
        
        # Keep only first N columns
        columns = profile.get("columns", {})
        for i, (col, stats) in enumerate(columns.items()):
            if i >= max_columns:
                break
            truncated["columns"][col] = stats
        
        if len(columns) > max_columns:
            logger.warning(f"Truncated profile: {len(columns)} -> {max_columns} columns")
        
        return truncated
    
    def _validate_recipe(self, recipe: CleaningRecipe, profile: Dict) -> CleaningRecipe:
        """
        Sanity check AI recipe against profile.
        
        CRITICAL: Prevent nonsensical suggestions
        """
        columns = profile.get("columns", {})
        
        # Check target column exists and is valid
        if recipe.target_column and recipe.target_column not in columns:
            logger.warning(f"Invalid target column '{recipe.target_column}', setting to None")
            recipe.target_column = None
        
        # Check type conversions reference real columns
        valid_conversions = {}
        for col, dtype in recipe.type_conversions.items():
            if col in columns:
                valid_conversions[col] = dtype
            else:
                logger.warning(f"Ignoring conversion for non-existent column '{col}'")
        recipe.type_conversions = valid_conversions
        
        # Check drop columns exist
        valid_drops = [c for c in recipe.drop_columns if c in columns]
        if len(valid_drops) < len(recipe.drop_columns):
            logger.warning(f"Some drop columns don't exist, filtered list")
        recipe.drop_columns = valid_drops
        
        # Sanity check: Can't impute categorical with mean/median
        if recipe.impute_strategy in ['mean', 'median']:
            # Check if any columns with nulls are categorical
            for col, stats in columns.items():
                if stats.get("null_percentage", 0) > 0 and stats.get("type") == "categorical":
                    logger.warning(f"Can't use {recipe.impute_strategy} on categorical data, switching to 'mode'")
                    recipe.impute_strategy = "mode"
                    break
        
        return recipe
    
    def _get_default_recipe(self, profile: Dict) -> CleaningRecipe:
        """
        Smarter Fallback Recipe (when AI is offline).
        
        Logic:
        1. Drop columns with >90% missing values (garbage columns).
        2. Impute remaining missing values with 'mean' (numeric) or 'mode' (categorical).
        3. Do NOT use 'drop_rows' as default, it destroys datasets like breast_cancer (all-null column).
        """
        insights = profile.get("insights", {})
        columns = profile.get("columns", {})
        
        # 1. Identify garbage columns
        drop_cols = []
        for col, stats in columns.items():
            if stats.get("null_percentage", 0) > 90.0:
                drop_cols.append(col)
                
        # 2. Find target
        target_candidates = insights.get("target_candidates", [])
        target = target_candidates[0] if target_candidates else None
        
        return CleaningRecipe(
            target_column=target,
            outlier_strategy="keep",
            impute_strategy="mode",  # Safer than drop_rows
            type_conversions={},
            drop_columns=drop_cols,
            confidence=0.5,
            reasoning="Smarter fallback: Drops empty cols, imputes using mode."
        )
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()


# Test function
async def test_ai_decision():
    """Test AI decision maker with sample profile"""
    # Sample profile (from profiler test)
    sample_profile = {
        "dataset_info": {"total_rows": 1000, "total_columns": 5},
        "insights": {
            "target_candidates": ["city"],
            "has_temporal": True,
            "high_missing_columns": []
        },
        "columns": {
            "user_id": {
                "type": "numeric",
                "null_percentage": 0.0,
                "domain_hint": "identifier"
            },
            "age": {
                "type": "numeric",
                "null_percentage": 0.0,
                "outlier_count": 100,
                "outlier_percentage": 10.0,
                "domain_hint": "age"
            },
            "income": {
                "type": "numeric",
                "null_percentage": 0.0,
                "outlier_count": 100,
                "outlier_percentage": 10.0,
                "domain_hint": "price"
            },
            "city": {
                "type": "categorical",
                "unique_count": 3,
                "is_high_cardinality": False
            },
            "signup_date": {
                "type": "temporal",
                "is_monotonic": True
            }
        }
    }
    
    print(f"\n{'='*60}")
    print("AI Decision Maker Test")
    print(f"{'='*60}\n")
    
    decision_maker = AIDecisionMaker(use_local_llm=True)
    
    print("Asking LM Studio for cleaning recipe...\n")
    recipe = await decision_maker.get_cleaning_recipe(sample_profile)
    
    print(f"Cleaning Recipe:")
    print(f"  Target Column: {recipe.target_column}")
    print(f"  Outlier Strategy: {recipe.outlier_strategy}")
    print(f"  Impute Strategy: {recipe.impute_strategy}")
    print(f"  Type Conversions: {recipe.type_conversions}")
    print(f"  Drop Columns: {recipe.drop_columns}")
    print(f"  Confidence: {recipe.confidence:.2f}")
    print(f"  Reasoning: {recipe.reasoning}\n")
    
    print(f"{'='*60}")
    if recipe.confidence > 0.5:
        print("✅ AI decision maker working!")
    else:
        print("⚠️  Using fallback recipe (AI unavailable)")
    print(f"{'='*60}\n")
    
    await decision_maker.close()


if __name__ == "__main__":
    asyncio.run(test_ai_decision())
