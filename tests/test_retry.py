"""
Tests for Retry Logic

Validates exponential backoff and retry behavior.
"""

import pytest
import asyncio
import httpx
from src.utils.retry import retry_with_backoff, retry_api_call


class TestRetryLogic:
    """Test suite for retry logic"""
    
    @pytest.mark.asyncio
    async def test_successful_first_attempt(self):
        """Test function succeeds on first attempt"""
        call_count = 0
        
        @retry_api_call
        async def always_succeeds():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await always_succeeds()
        
        assert result == "success"
        assert call_count == 1  # Only called once
    
    @pytest.mark.asyncio
    async def test_retry_on_rate_limit(self):
        """Test retry on 429 rate limit error"""
        call_count = 0
        
        @retry_with_backoff(max_attempts=3, base_delay=0.1)
        async def flaky_api():
            nonlocal call_count
            call_count += 1
            
            if call_count < 3:
                # Simulate 429 rate limit
                response = httpx.Response(
                    status_code=429,
                    request=httpx.Request("GET", "http://test.com")
                )
                raise httpx.HTTPStatusError(
                    "Rate limited",
                    request=response.request,
                    response=response
                )
            
            return "success"
        
        result = await flaky_api()
        
        assert result == "success"
        assert call_count == 3  # Retried 2 times
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Test max retries causes failure"""
        call_count = 0
        
        @retry_with_backoff(max_attempts=3, base_delay=0.1)
        async def always_fails():
            nonlocal call_count
            call_count += 1
            
            response = httpx.Response(
                status_code=429,
                request=httpx.Request("GET", "http://test.com")
            )
            raise httpx.HTTPStatusError(
                "Rate limited",
                request=response.request,
                response=response
            )
        
        with pytest.raises(httpx.HTTPStatusError):
            await always_fails()
        
        assert call_count == 3  # Max attempts reached
    
    @pytest.mark.asyncio
    async def test_no_retry_on_4xx_errors(self):
        """Test 4xx errors (except 429) don't retry"""
        call_count = 0
        
        @retry_api_call
        async def client_error():
            nonlocal call_count
            call_count += 1
            
            response = httpx.Response(
                status_code=404,
                request=httpx.Request("GET", "http://test.com")
            )
            raise httpx.HTTPStatusError(
                "Not found",
                request=response.request,
                response=response
            )
        
        with pytest.raises(httpx.HTTPStatusError):
            await client_error()
        
        assert call_count == 1  # No retry on 404
    
    def test_sync_retry(self):
        """Test synchronous retry wrapper"""
        call_count = 0
        
        @retry_with_backoff(max_attempts=2, base_delay=0.1)
        def sync_function():
            nonlocal call_count
            call_count += 1
            
            if call_count < 2:
                raise ConnectionError("Temporary failure")
            
            return "success"
        
        result = sync_function()
        
        assert result == "success"
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_exponential_backoff_timing(self):
        """Test exponential backoff increases delay"""
        import time
        call_times = []
        
        @retry_with_backoff(max_attempts=3, base_delay=0.1, exponential_base=2.0, jitter=False)
        async def timed_retry():
            call_times.append(time.time())
            
            if len(call_times) < 3:
                raise ConnectionError("Temporary failure")
            
            return "success"
        
        await timed_retry()
        
        # Check delays increased (approximately)
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]
        
        assert delay1 >= 0.1  # First delay: 0.1s
        assert delay2 >= 0.2  # Second delay: 0.2s (exponential)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
