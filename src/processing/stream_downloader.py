import asyncio
import httpx
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class StreamDownloader:
    """
    Memory-safe file downloader using chunked streaming.
    **GUARDRAIL: Prevents memory bombs by never loading full file in RAM**
    """
    
    def __init__(self, max_file_size_mb: int = 500):
        """
        Args:
            max_file_size_mb: Maximum allowed file size in MB (default: 500MB)
        """
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.client = httpx.AsyncClient(timeout=300.0, follow_redirects=True)
    
    async def download_chunked(
        self,
        url: str,
        output_path: Path,
        chunk_size: int = 8192  # 8KB chunks
    ) -> Optional[Path]:
        """
        Download file in chunks (streaming) to prevent memory overflow.
        
        Args:
            url: URL to download from
            output_path: Where to save the file
            chunk_size: Size of each chunk in bytes (default: 8KB)
            
        Returns:
            Path to downloaded file or None if failed
        """
        try:
            logger.info(f"Starting chunked download: {url}")
            
            # Create output directory if needed
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Stream the response
            async with self.client.stream("GET", url) as response:
                response.raise_for_status()
                
                # Check file size from headers
                content_length = response.headers.get("content-length")
                if content_length:
                    file_size = int(content_length)
                    if file_size > self.max_file_size_bytes:
                        logger.error(
                            f"File too large: {file_size / (1024*1024):.1f}MB "
                            f"(max: {self.max_file_size_bytes / (1024*1024):.0f}MB)"
                        )
                        return None
                    
                    logger.info(f"File size: {file_size / (1024*1024):.1f}MB")
                
                # Download in chunks
                downloaded_bytes = 0
                with open(output_path, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size):
                        f.write(chunk)
                        downloaded_bytes += len(chunk)
                        
                        # Safety check: Stop if exceeding max size
                        if downloaded_bytes > self.max_file_size_bytes:
                            logger.error(f"Download exceeded max size, aborting")
                            output_path.unlink()  # Delete partial file
                            return None
                        
                        # Progress logging (every 10MB)
                        if downloaded_bytes % (10 * 1024 * 1024) < chunk_size:
                            logger.info(f"Downloaded: {downloaded_bytes / (1024*1024):.1f}MB")
            
            logger.info(f"✅ Download complete: {output_path}")
            logger.info(f"   Total size: {downloaded_bytes / (1024*1024):.1f}MB")
            return output_path
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error downloading {url}: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            if output_path.exists():
                output_path.unlink()  # Clean up partial file
            return None
    
    async def get_file_size(self, url: str) -> Optional[int]:
        """
        Get file size without downloading (HEAD request).
        
        Args:
            url: URL to check
            
        Returns:
            File size in bytes or None if unavailable
        """
        try:
            response = await self.client.head(url)
            content_length = response.headers.get("content-length")
            if content_length:
                return int(content_length)
            return None
        except Exception as e:
            logger.warning(f"Could not get file size for {url}: {e}")
            return None
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Test function
async def test_stream_downloader():
    """Test stream downloader with a real file"""
    downloader = StreamDownloader(max_file_size_mb=50)  # 50MB limit for test
    
    # Test URL (small CSV file from GitHub)
    test_url = "https://raw.githubusercontent.com/datasets/gdp/master/data/gdp.csv"
    output_path = Path("downloads/test_gdp.csv")
    
    print(f"\n{'='*60}")
    print("Stream Downloader Test (Memory Bomb Prevention)")
    print(f"{'='*60}\n")
    
    # Check file size first
    print(f"Checking file size...")
    file_size = await downloader.get_file_size(test_url)
    if file_size:
        print(f"File size: {file_size / 1024:.1f}KB\n")
    
    # Download
    print(f"Downloading: {test_url}")
    print(f"Output: {output_path}\n")
    
    result = await downloader.download_chunked(test_url, output_path)
    
    if result and result.exists():
        actual_size = result.stat().st_size
        print(f"\n✅ Download successful!")
        print(f"   File saved: {result}")
        print(f"   Size: {actual_size / 1024:.1f}KB")
        
        # Verify memory safety
        print(f"\n🛡️  Memory Safety:")
        print(f"   Max allowed: {downloader.max_file_size_bytes / (1024*1024):.0f}MB")
        print(f"   Downloaded: {actual_size / (1024*1024):.2f}MB")
        print(f"   Status: {'✅ Safe' if actual_size < downloader.max_file_size_bytes else '❌ Exceeded'}")
    else:
        print(f"\n❌ Download failed")
    
    await downloader.close()
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(test_stream_downloader())
