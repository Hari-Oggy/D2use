import asyncio
import json
import re
from typing import Dict, Optional
import httpx
import logging

from ..config import settings

logger = logging.getLogger(__name__)

# LM Studio endpoint from settings
# Uses settings.LLM_ENDPOINT from config.py

class LLMExtractor:
    """
    Uses Local LLM (via LM Studio) or Gemini Flash API to extract structured metadata from HTML.
    Falls back to regex extraction if both fail.
    """
    
    def __init__(self, use_local_llm: bool = True):
        """
        Args:
            use_local_llm: If True, try LM Studio first, then Gemini. If False, use Gemini only.
        """
        self.use_local_llm = use_local_llm
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Only import Gemini if needed
        if not use_local_llm or settings.GEMINI_API_KEY != "your_gemini_api_key_here":
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.gemini_model = genai.GenerativeModel("gemini-2.5-flash")
            except:
                self.gemini_model = None
        else:
            self.gemini_model = None
    
    async def extract_metadata(self, html: str, url: str) -> Optional[Dict]:
        """
        Extract dataset metadata from HTML using LLM (local or cloud) with fallbacks.
        
        Priority:
        1. LM Studio (local LLM) - No API costs, no quotas
        2. Gemini Flash - Cloud fallback
        3. Regex extraction - Simple pattern matching
        
        Args:
            html: HTML content of the page
            url: URL of the page (for context)
            
        Returns:
            Dict with extracted metadata
        """
        # Try LM Studio (local LLM) first
        if self.use_local_llm:
            try:
                result = await self._extract_with_lmstudio(html, url)
                if result:
                    logger.info(f"✅ Metadata extracted using LM Studio (local LLM)")
                    return result
            except Exception as e:
                logger.warning(f"LM Studio extraction failed: {e}")
        
        # Fallback to Gemini
        if self.gemini_model:
            try:
                result = await self._extract_with_gemini(html, url)
                if result:
                    logger.info(f"✅ Metadata extracted using Gemini Flash")
                    return result
            except Exception as e:
                if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                    logger.warning(f"Gemini quota exceeded: {e}")
                else:
                    logger.warning(f"Gemini extraction failed: {e}")
        
        # Final fallback to regex
        logger.warning("Using regex fallback for metadata extraction")
        return self._extract_with_regex(html, url)
    
    async def _extract_with_lmstudio(self, html: str, url: str) -> Optional[Dict]:
        """Extract metadata using LM Studio local LLM"""
        truncated_html = html[:10000]
        
        prompt = f"""You are a dataset metadata extractor. Analyze this webpage and extract dataset information.

URL: {url}

HTML Content (truncated):
{truncated_html}

Extract the following information and return ONLY a valid JSON object:
{{
    "dataset_name": "name of the dataset",
    "description": "brief description",
    "file_size_mb": estimated size in MB (number only, or 0 if unknown),
    "file_format": "csv/json/parquet/zip/unknown",
    "download_url": "direct download link if found, or empty string",
    "license": "license type if mentioned, or 'unknown'",
    "tags": ["tag1", "tag2"]
}}

Return ONLY the JSON, no additional text."""
        
        payload = {
            "model": settings.LLM_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": settings.LLM_TEMP_METADATA_EXTRACTION,
            "max_tokens": settings.LLM_MAX_TOKENS
        }
        
        response = await self.http_client.post(settings.LLM_ENDPOINT, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        # LM Studio 0.4.0 response format
        if "choices" in data and len(data["choices"]) > 0:
            content = data["choices"][0]["message"]["content"].strip()
        elif "message" in data:
            content = data["message"]["content"].strip()
        else:
            raise ValueError(f"Unexpected LM Studio response format: {data}")
        
        # Parse JSON from response
        return self._parse_json_response(content)
    
    async def _extract_with_gemini(self, html: str, url: str) -> Optional[Dict]:
        """Extract metadata using Gemini Flash API"""
        truncated_html = html[:10000]
        
        prompt = f"""You are a dataset metadata extractor. Analyze this webpage and extract dataset information.

URL: {url}

HTML Content (truncated):
{truncated_html}

Extract the following information and return ONLY a valid JSON object:
{{
    "dataset_name": "name of the dataset",
    "description": "brief description",
    "file_size_mb": estimated size in MB (number only, or 0 if unknown),
    "file_format": "csv/json/parquet/zip/unknown",
    "download_url": "direct download link if found, or empty string",
    "license": "license type if mentioned, or 'unknown'",
    "tags": ["tag1", "tag2"]
}}

Return ONLY the JSON, no additional text."""
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.gemini_model.generate_content(prompt)
        )
        
        content = response.text.strip()
        return self._parse_json_response(content)
    
    def _parse_json_response(self, content: str) -> Optional[Dict]:
        """Parse JSON from LLM response, handling markdown code blocks"""
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
    
    def _extract_with_regex(self, html: str, url: str) -> Dict:
        """Fallback: Extract metadata using regex patterns"""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title
        title = soup.title.string if soup.title else ""
        dataset_name = title.split("-")[0].strip() if title else url.split("/")[-1]
        
        # Extract file size
        size_mb = 0.0
        size_match = re.search(r'(\d+\.?\d*)\s*(MB|KB|GB)', html, re.IGNORECASE)
        if size_match:
            value, unit = size_match.groups()
            value = float(value)
            if unit.upper() == "KB":
                size_mb = value / 1024
            elif unit.upper() == "GB":
                size_mb = value * 1024
            else:
                size_mb = value
        
        # Extract file format from URL or HTML
        file_format = "unknown"
        for ext in [".csv", ".json", ".parquet", ".zip", ".xlsx"]:
            if ext in url.lower() or ext in html.lower():
                file_format = ext[1:]  # Remove dot
                break
        
        # Extract license
        license_type = "unknown"
        license_patterns = ["MIT", "Apache", "CC-BY", "CC0", "GPL", "BSD"]
        for lic in license_patterns:
            if lic in html:
                license_type = lic
                break
        
        # Extract download URL
        download_url = ""
        download_link = soup.find("a", href=re.compile(r'\.(csv|json|zip|parquet)'))
        if download_link:
            download_url = download_link.get("href", "")
        
        return {
            "dataset_name": dataset_name,
            "description": f"Dataset from {url}",
            "file_size_mb": size_mb,
            "file_format": file_format,
            "download_url": download_url,
            "license": license_type,
            "tags": []
        }
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()


# Test function
async def test_llm_extractor():
    """Test the LLM extractor with all fallback levels"""
    print(f"\n{'='*60}")
    print("LLM Metadata Extractor Test (with fallbacks)")
    print(f"{'='*60}\n")
    
    # Sample HTML
    sample_html = """
    <html>
    <head><title>Breast Cancer Wisconsin Dataset - UCI</title></head>
    <body>
        <h1>Breast Cancer Wisconsin Dataset</h1>
        <p>Features computed from digitized images of breast mass.</p>
        <p>File size: 25 KB</p>
        <p>Format: CSV</p>
        <p>License: CC BY 4.0</p>
        <a href="/download/cancer.csv">Download CSV</a>
        <div>Tags: healthcare, classification, medical</div>
    </body>
    </html>
    """
    
    # Test with local LLM first
    extractor = LLMExtractor(use_local_llm=True)
    
    try:
        metadata = await extractor.extract_metadata(sample_html, "https://example.com/cancer-dataset")
        
        if metadata:
            print("✅ Metadata extraction successful!\n")
            print(json.dumps(metadata, indent=2))
        else:
            print("❌ Metadata extraction failed")
    finally:
        await extractor.close()
    
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(test_llm_extractor())

