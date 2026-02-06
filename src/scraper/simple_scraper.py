import asyncio
import httpx
from typing import Dict, Optional
from bs4 import BeautifulSoup
import logging

from .circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)

class SimpleHTTPScraper:
    """
    Simple HTTP scraper using httpx + BeautifulSoup.
    Lightweight alternative to Crawlee for static pages.
    Integrates with Circuit Breaker.
    """
    
    def __init__(self):
        self.circuit_breaker = CircuitBreaker()
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )
    
    async def scrape_url(self, url: str) -> Optional[Dict]:
        """
        Scrape a URL and extract metadata.
        
        Args:
            url: URL to scrape
            
        Returns:
            Dict with HTML content, title, and metadata, or None if failed
        """
        # Check circuit breaker
        if not self.circuit_breaker.can_request(url):
            logger.warning(f"Circuit breaker blocked request to {url}")
            return None
        
        try:
            logger.info(f"Scraping URL: {url}")
            
            # Fetch page
            response = await self.client.get(url)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract data
            scraped_data = {
                "url": url,
                "title": soup.title.string if soup.title else "",
                "html": response.text,
                "download_links": [],
                "page_text": ""
            }
            
            # Find download links
            for link in soup.find_all("a", href=True):
                href = link.get("href")
                text = link.get_text(strip=True)
                
                # Check if it's a dataset file
                if any(ext in href.lower() for ext in [".csv", ".json", ".zip", ".parquet", "download"]):
                    scraped_data["download_links"].append({
                        "href": href,
                        "text": text
                    })
                    
                    if len(scraped_data["download_links"]) >= 10:
                        break
            
            # Extract visible text (first 5000 chars)
            page_text = soup.get_text(separator=" ", strip=True)
            scraped_data["page_text"] = page_text[:5000]
            
            # Record success
            self.circuit_breaker.record_success(url)
            
            logger.info(f"Successfully scraped {url}")
            return scraped_data
            
        except httpx.HTTPStatusError as e:
            self.circuit_breaker.record_failure(url)
            logger.error(f"HTTP error scraping {url}: {e.response.status_code}")
            return None
        except Exception as e:
            self.circuit_breaker.record_failure(url)
            logger.error(f"Failed to scrape {url}: {e}")
            return None
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Test function
async def test_simple_scraper():
    """Test the simple HTTP scraper"""
    scraper = SimpleHTTPScraper()
    
    # Test with a known dataset URL
    test_url = "https://github.com/datasets/gdp"
    
    print(f"\n{'='*60}")
    print(f"Simple HTTP Scraper Test")
    print(f"{'='*60}\n")
    print(f"Scraping: {test_url}\n")
    
    try:
        result = await scraper.scrape_url(test_url)
        
        if result:
            print("✅ Scraping successful!\n")
            print(f"Title: {result.get('title', 'N/A')}")
            print(f"Download links found: {len(result.get('download_links', []))}")
            print(f"HTML length: {len(result.get('html', ''))} characters")
            print(f"Page text length: {len(result.get('page_text', ''))} characters")
            
            if result.get('download_links'):
                print("\nSample download links:")
                for i, link in enumerate(result['download_links'][:3], 1):
                    print(f"  {i}. {link['text']}: {link['href'][:60]}...")
        else:
            print("❌ Scraping failed")
    finally:
        await scraper.close()
    
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(test_simple_scraper())
