from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    """
    Application settings loaded from .env file with strict validation.
    """
    # API Keys (Required)
    HF_TOKEN: str = Field(..., description="Hugging Face API Token")
    KAGGLE_USERNAME: str = Field(..., description="Kaggle Username")
    KAGGLE_KEY: str = Field(..., description="Kaggle API Key")
    SERPAPI_KEY: str = Field(..., description="SerpAPI Key for web search")
    GEMINI_API_KEY: str = Field(..., description="Google Gemini API Key")

    # LLM Configuration (Optional - with defaults)
    USE_LOCAL_LLM: bool = Field(default=True, description="Enable local LLM via LM Studio")
    LLM_MODEL: str = Field(default="qwen2.5-7b-instruct", description="LLM model identifier")
    LLM_ENDPOINT: str = Field(default="http://localhost:1234/v1/chat/completions", description="LM Studio endpoint")
    LLM_TIMEOUT: int = Field(default=60, description="LLM request timeout in seconds")
    LLM_MAX_TOKENS: int = Field(default=2000, description="Maximum tokens in LLM response")
    
    # Task-specific LLM temperatures (different tasks need different creativity levels)
    LLM_TEMPERATURE: float = Field(default=0.2, description="Default LLM temperature")
    LLM_TEMP_QUERY_EXPANSION: float = Field(default=0.3, description="Higher for creative search terms")
    LLM_TEMP_SCHEMA_CLEANING: float = Field(default=0.1, description="Lower for precise column naming")
    LLM_TEMP_METADATA_EXTRACTION: float = Field(default=0.1, description="Lower for accurate extraction")
    LLM_TEMP_AI_DECISION: float = Field(default=0.2, description="Balanced for cleaning decisions")
    
    # File Processing Limits (Optional - with defaults)
    MAX_FILE_SIZE_MB: int = Field(default=500, description="Maximum downloadable file size in MB")
    MAX_DATASET_ROWS: int = Field(default=10000, description="Maximum rows to process")
    CHUNK_SIZE_KB: int = Field(default=8, description="Download chunk size in KB")
    
    # API Server Configuration (Optional - with defaults)
    API_HOST: str = Field(default="0.0.0.0", description="FastAPI host")
    API_PORT: int = Field(default=8000, description="FastAPI port")
    API_WORKERS: int = Field(default=1, description="Number of Uvicorn workers")
    
    # Paths (Optional - with defaults)
    OUTPUT_DIR: str = Field(default="output", description="Output directory for processed datasets")
    CACHE_DIR: str = Field(default="cache", description="Cache directory for downloads")
    KAGGLE_TEMP_DIR: str = Field(default="_kaggle_tmp", description="Temporary directory for Kaggle downloads")
    
    # Circuit Breaker (Optional - with defaults)
    CIRCUIT_BREAKER_THRESHOLD: int = Field(default=5, description="Failures before circuit opens")
    CIRCUIT_BREAKER_WINDOW_SECONDS: int = Field(default=300, description="Time window for failure tracking")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Ignore extra fields in .env
    )

settings = Settings()
