import asyncio
from typing import Dict, Optional

import logging

from .circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)

class CrawleeEngine:
    """
    Resilient web scraper using Crawlee + Playwright.
    Integrates with Circuit Breaker to prevent hammering blocked sites.
    """
    
    def __init__(self):
        self.circuit_breaker = CircuitBreaker()
        self.results: Dict[str, Dict] = {}
    
    async def scrape_url(self, url: str, timeout: int = 30000) -> Optional[Dict]:
        """
        Scrape a URL and extract metadata using raw Playwright.
        """
        # Check circuit breaker
        if not self.circuit_breaker.can_request(url):
            logger.warning(f"Circuit breaker blocked request to {url}")
            return None
        
        try:
            logger.info(f"Scraping URL: {url}")
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Set timeout
                page.set_default_timeout(timeout)
                
                try:
                    await page.goto(url, wait_until="domcontentloaded")
                    
                    # Extract data
                    scraped_data = {}
                    scraped_data["url"] = url
                    scraped_data["title"] = await page.title()
                    scraped_data["html"] = await page.content()
                    
                    # Try to find download links
                    download_links = []
                    # Selector for common dataset links (Specific + Generic)
                    # GitHub uses blob/.../file.csv. We target these specifically.
                    elements = await page.query_selector_all("a[href*='.csv'], a[href*='.json'], a[href*='.parquet'], a[href*='download'], a[href]")
                    
                    found_links = set()
                    
                    for element in elements[:200]: # Check up to 200 links
                        href = await element.get_attribute("href")
                        text = await element.inner_text() or ""
                        
                        if not href: continue
                        
                        # Dedup
                        if href in found_links: continue
                        found_links.add(href)
                        
                        # Filter
                        lower_href = href.lower()
                        valid_exts = ['.csv', '.json', '.parquet', '.zip', '.xls', 'download', 'raw']
                        if any(ext in lower_href for ext in valid_exts):
                            # GitHub Helper: Convert blob -> raw for direct download
                            if "github.com" in url or "github.com" in href:
                                if "/blob/" in href:
                                    href = href.replace("/blob/", "/raw/")
                                    
                            download_links.append({"href": href, "text": text.strip()})
                    
                    scraped_data["download_links"] = download_links
                    
                    # Try to extract text
                    text_content = await page.inner_text("body")
                    scraped_data["page_text"] = text_content[:5000] if text_content else ""
                    
                    self.circuit_breaker.record_success(url)
                    logger.info(f"Successfully scraped {url}. Found {len(download_links)} links.")
                    
                    await browser.close()
                    return scraped_data
                    
                except Exception as e:
                    await browser.close()
                    raise e
            
        except Exception as e:
            # Record failure
            self.circuit_breaker.record_failure(url)
            logger.error(f"Failed to scrape {url}: {e}")
            return None


# Test function
async def test_crawlee_engine():
    """Test the Crawlee engine"""
    engine = CrawleeEngine()
    
    # Test with a known dataset URL
    test_url = "https://github.com/datasets/gdp"
    
    print(f"\n{'='*60}")
    print(f"Crawlee Engine Test")
    print(f"{'='*60}\n")
    print(f"Scraping: {test_url}\n")
    
    result = await engine.scrape_url(test_url)
    
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
    
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(test_crawlee_engine())
