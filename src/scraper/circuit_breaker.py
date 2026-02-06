import time
from enum import Enum
from typing import Dict, Optional
from collections import defaultdict, deque
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Blocking requests (too many failures)
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    """
    GUARDRAIL: Circuit Breaker
    
    Prevents the scraper from hammering websites that are blocking or failing.
    Tracks failure rates per domain and implements exponential backoff.
    """
    
    def __init__(
        self,
        failure_threshold: float = 0.3,  # 30% failure rate triggers OPEN (production-ready)
        window_size: int = 10,            # Track last 10 requests per domain
        open_duration: int = 60,          # Stay OPEN for 60 seconds
        half_open_max_requests: int = 3   # Test with 3 requests in HALF_OPEN
    ):
        self.failure_threshold = failure_threshold
        self.window_size = window_size
        self.open_duration = open_duration
        self.half_open_max_requests = half_open_max_requests
        
        # Track state per domain
        self.states: Dict[str, CircuitState] = defaultdict(lambda: CircuitState.CLOSED)
        self.failure_counts: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        self.open_times: Dict[str, float] = {}
        self.half_open_attempts: Dict[str, int] = defaultdict(int)
    
    def _get_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            return urlparse(url).netloc
        except:
            return url
    
    def can_request(self, url: str) -> bool:
        """
        Check if a request to this URL is allowed.
        
        Args:
            url: URL to check
            
        Returns:
            True if request is allowed, False if circuit is OPEN
        """
        domain = self._get_domain(url)
        state = self.states[domain]
        
        if state == CircuitState.CLOSED:
            return True
        
        elif state == CircuitState.OPEN:
            # Check if enough time has passed to try HALF_OPEN
            if time.time() - self.open_times[domain] >= self.open_duration:
                logger.info(f"Circuit breaker for {domain}: OPEN -> HALF_OPEN (testing recovery)")
                self.states[domain] = CircuitState.HALF_OPEN
                self.half_open_attempts[domain] = 0
                return True
            else:
                logger.warning(f"Circuit breaker OPEN for {domain} - request blocked")
                return False
        
        elif state == CircuitState.HALF_OPEN:
            # Allow limited requests to test recovery
            if self.half_open_attempts[domain] < self.half_open_max_requests:
                self.half_open_attempts[domain] += 1
                return True
            else:
                logger.warning(f"Circuit breaker HALF_OPEN limit reached for {domain}")
                return False
        
        return False
    
    def record_success(self, url: str):
        """Record a successful request"""
        domain = self._get_domain(url)
        self.failure_counts[domain].append(False)
        
        # If in HALF_OPEN and success, transition to CLOSED
        if self.states[domain] == CircuitState.HALF_OPEN:
            logger.info(f"Circuit breaker for {domain}: HALF_OPEN -> CLOSED (recovered)")
            self.states[domain] = CircuitState.CLOSED
            self.half_open_attempts[domain] = 0
    
    def record_failure(self, url: str):
        """Record a failed request"""
        domain = self._get_domain(url)
        self.failure_counts[domain].append(True)
        
        # Calculate failure rate
        failures = self.failure_counts[domain]
        if len(failures) >= self.window_size:
            failure_rate = sum(failures) / len(failures)
            
            if failure_rate >= self.failure_threshold:
                # Transition to OPEN
                if self.states[domain] != CircuitState.OPEN:
                    logger.warning(
                        f"Circuit breaker for {domain}: {self.states[domain].value} -> OPEN "
                        f"(failure rate: {failure_rate:.1%})"
                    )
                    self.states[domain] = CircuitState.OPEN
                    self.open_times[domain] = time.time()
    
    def get_state(self, url: str) -> CircuitState:
        """Get current circuit state for a URL"""
        domain = self._get_domain(url)
        return self.states[domain]
    
    def get_stats(self, url: str) -> Dict:
        """Get statistics for a domain"""
        domain = self._get_domain(url)
        failures = self.failure_counts[domain]
        
        return {
            "domain": domain,
            "state": self.states[domain].value,
            "total_requests": len(failures),
            "failure_rate": sum(failures) / len(failures) if failures else 0.0,
            "failures": sum(failures),
            "successes": len(failures) - sum(failures)
        }


# Test function
def test_circuit_breaker():
    """Test the circuit breaker"""
    print(f"\n{'='*60}")
    print("Circuit Breaker Test")
    print(f"{'='*60}\n")
    
    cb = CircuitBreaker(failure_threshold=0.5, window_size=5)
    test_url = "https://example.com/data.csv"
    
    # Simulate requests
    print("Simulating 10 requests (5 failures, 5 successes):\n")
    
    for i in range(10):
        if cb.can_request(test_url):
            # Simulate failure for odd numbers
            if i % 2 == 1:
                cb.record_failure(test_url)
                print(f"Request {i+1}: ❌ FAILED")
            else:
                cb.record_success(test_url)
                print(f"Request {i+1}: ✅ SUCCESS")
            
            stats = cb.get_stats(test_url)
            print(f"  State: {stats['state'].upper()} | Failure rate: {stats['failure_rate']:.1%}\n")
        else:
            print(f"Request {i+1}: 🚫 BLOCKED (circuit OPEN)\n")
    
    print(f"{'='*60}")
    print("Final Stats:")
    print(f"{'='*60}")
    stats = cb.get_stats(test_url)
    for key, value in stats.items():
        print(f"{key}: {value}")
    print()


if __name__ == "__main__":
    test_circuit_breaker()
