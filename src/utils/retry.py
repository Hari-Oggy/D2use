"""
Retry Logic with Exponential Backoff

Handles transient failures in API calls and network requests.
Implements exponential backoff with jitter to prevent thundering herd.
"""

import asyncio
import random
import logging
from functools import wraps
from typing import Callable, TypeVar, Any, Tuple, Type
import httpx

logger = logging.getLogger(__name__)

T = TypeVar('T')


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (
        httpx.HTTPStatusError,
        httpx.TimeoutException,
        httpx.ConnectError,
        httpx.ReadTimeout,
        ConnectionError
    )
):
    """
    Decorator for retry logic with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential calculation (2.0 = doubles each time)
        jitter: Add random jitter to prevent thundering herd
        exceptions: Tuple of exceptions to catch and retry
        
    Example:
        @retry_with_backoff(max_attempts=3, base_delay=1.0)
        async def download_dataset(url):
            response = await client.get(url)
            return response.json()
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            attempt = 0
            last_exception = None
            
            while attempt < max_attempts:
                try:
                    return await func(*args, **kwargs)
                    
                except exceptions as e:
                    attempt += 1
                    last_exception = e
                    
                    # Don't retry 4xx errors (except 429 Too Many Requests)
                    if isinstance(e, httpx.HTTPStatusError):
                        if 400 <= e.response.status_code < 500:
                            if e.response.status_code != 429:  # Rate limit
                                logger.error(f"Client error {e.response.status_code}, not retrying")
                                raise
                    
                    if attempt >= max_attempts:
                        logger.error(f"❌ Max retries ({max_attempts}) exceeded for {func.__name__}")
                        raise last_exception
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** (attempt - 1)), max_delay)
                    
                    # Add jitter (random 0-100% of delay)
                    if jitter:
                        delay = delay * (0.5 + random.random() * 0.5)
                    
                    logger.warning(
                        f"⚠️ Retry {attempt}/{max_attempts} for {func.__name__} "
                        f"after {delay:.1f}s (error: {type(e).__name__})"
                    )
                    
                    await asyncio.sleep(delay)
                
                except Exception as e:
                    # Unexpected exception, don't retry
                    logger.error(f"❌ Unexpected error in {func.__name__}: {e}")
                    raise
            
            # Should never reach here
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            """Synchronous version of retry wrapper"""
            import time
            attempt = 0
            last_exception = None
            
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                    
                except exceptions as e:
                    attempt += 1
                    last_exception = e
                    
                    # Don't retry 4xx errors (except 429)
                    if isinstance(e, httpx.HTTPStatusError):
                        if 400 <= e.response.status_code < 500:
                            if e.response.status_code != 429:
                                logger.error(f"Client error {e.response.status_code}, not retrying")
                                raise
                    
                    if attempt >= max_attempts:
                        logger.error(f"❌ Max retries ({max_attempts}) exceeded for {func.__name__}")
                        raise last_exception
                    
                    delay = min(base_delay * (exponential_base ** (attempt - 1)), max_delay)
                    
                    if jitter:
                        delay = delay * (0.5 + random.random() * 0.5)
                    
                    logger.warning(
                        f"⚠️ Retry {attempt}/{max_attempts} for {func.__name__} "
                        f"after {delay:.1f}s (error: {type(e).__name__})"
                    )
                    
                    time.sleep(delay)
                
                except Exception as e:
                    logger.error(f"❌ Unexpected error in {func.__name__}: {e}")
                    raise
            
            raise last_exception
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Convenience decorators for common scenarios

def retry_api_call(func: Callable[..., T]) -> Callable[..., T]:
    """
    Standard retry for API calls.
    - 3 attempts
    - 1s base delay
    - Exponential backoff
    """
    return retry_with_backoff(
        max_attempts=3,
        base_delay=1.0,
        exponential_base=2.0,
        jitter=True
    )(func)


def retry_download(func: Callable[..., T]) -> Callable[..., T]:
    """
    Retry for file downloads (more aggressive).
    - 5 attempts
    - 2s base delay
    - Max 30s delay
    """
    return retry_with_backoff(
        max_attempts=5,
        base_delay=2.0,
        max_delay=30.0,
        exponential_base=2.0,
        jitter=True
    )(func)


def retry_network(func: Callable[..., T]) -> Callable[..., T]:
    """
    Retry for network operations (patient).
    - 10 attempts
    - 0.5s base delay
    - Max 10s delay
    """
    return retry_with_backoff(
        max_attempts=10,
        base_delay=0.5,
        max_delay=10.0,
        exponential_base=1.5,
        jitter=True
    )(func)


# Test function
async def test_retry_logic():
    """Test retry with simulated failures"""
    
    call_count = 0
    
    @retry_with_backoff(max_attempts=3, base_delay=0.5)
    async def flaky_function():
        nonlocal call_count
        call_count += 1
        
        if call_count < 3:
            # Simulate rate limiting
            response = httpx.Response(
                status_code=429,
                headers={"retry-after": "1"},
                request=httpx.Request("GET", "http://example.com")
            )
            raise httpx.HTTPStatusError(
                "Rate limited",
                request=response.request,
                response=response
            )
        
        return "Success!"
    
    print("Testing retry logic...")
    print("=" * 60)
    
    try:
        result = await flaky_function()
        print(f"✅ Result after {call_count} attempts: {result}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_retry_logic())
