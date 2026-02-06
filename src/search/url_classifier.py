import re
from typing import List
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

class URLClassifier:
    """
    GUARDRAIL: Junk Filter
    
    Classifies URLs to filter out blogs, news sites, and non-dataset content.
    Only allows URLs likely to contain actual datasets.
    """
    
    # Trusted domains that typically host datasets
    TRUSTED_DOMAINS = {
        "github.com",
        "raw.githubusercontent.com",
        "zenodo.org",
        "data.gov",
        "data.world",
        "figshare.com",
        "archive.ics.uci.edu",
        "kaggle.com",
        "huggingface.co",
        "datasets.huggingface.co",
        "drive.google.com",
        "dropbox.com",
        "s3.amazonaws.com",
        "storage.googleapis.com",
        "dataverse.harvard.edu",
        "openml.org",
        "datadryad.org"
    }
    
    # File extensions that indicate datasets
    DATASET_EXTENSIONS = {
        ".csv", ".json", ".jsonl", ".parquet", ".tsv", ".txt",
        ".xlsx", ".xls", ".xml", ".sql", ".db", ".sqlite",
        ".h5", ".hdf5", ".feather", ".arrow", ".zip", ".tar.gz",
        ".pkl", ".pickle", ".npy", ".npz"
    }
    
    # Patterns to REJECT (blogs, news, tutorials)
    JUNK_PATTERNS = [
        r"blog",
        r"news",
        r"article",
        r"tutorial",
        r"medium\.com",
        r"towardsdatascience\.com",
        r"reddit\.com",
        r"stackoverflow\.com",
        r"youtube\.com",
        r"twitter\.com",
        r"linkedin\.com",
        r"facebook\.com"
    ]
    
    def is_dataset_url(self, url: str) -> bool:
        """
        Determine if a URL is likely to point to a dataset.
        
        Args:
            url: URL to classify
            
        Returns:
            True if URL is likely a dataset, False if it's junk
        """
        try:
            parsed = urlparse(url.lower())
            domain = parsed.netloc.replace("www.", "")
            path = parsed.path
            
            # Check 1: Domain whitelist
            if any(trusted in domain for trusted in self.TRUSTED_DOMAINS):
                logger.debug(f"✅ URL passed domain whitelist: {url}")
                return True
            
            # Check 2: File extension check
            if any(path.endswith(ext) for ext in self.DATASET_EXTENSIONS):
                logger.debug(f"✅ URL passed file extension check: {url}")
                return True
            
            # Check 3: Reject junk patterns
            full_url = url.lower()
            for pattern in self.JUNK_PATTERNS:
                if re.search(pattern, full_url):
                    logger.debug(f"❌ URL rejected (junk pattern '{pattern}'): {url}")
                    return False
            
            # Check 4: Look for dataset-related keywords in path
            dataset_keywords = ["dataset", "data", "download", "file", "csv", "json"]
            if any(keyword in path for keyword in dataset_keywords):
                logger.debug(f"✅ URL passed keyword check: {url}")
                return True
            
            # Default: reject if no positive signals
            logger.debug(f"❌ URL rejected (no positive signals): {url}")
            return False
            
        except Exception as e:
            logger.warning(f"Error classifying URL {url}: {e}")
            return False
    
    def filter_urls(self, urls: List[str]) -> List[str]:
        """
        Filter a list of URLs, keeping only dataset URLs.
        
        Args:
            urls: List of URLs to filter
            
        Returns:
            Filtered list of dataset URLs
        """
        filtered = [url for url in urls if self.is_dataset_url(url)]
        
        logger.info(f"Filtered {len(urls)} URLs -> {len(filtered)} dataset URLs (removed {len(urls) - len(filtered)} junk)")
        
        return filtered


# Test function
def test_url_classifier():
    """Test the URL classifier"""
    classifier = URLClassifier()
    
    test_urls = [
        # Should PASS
        "https://github.com/user/repo/data.csv",
        "https://zenodo.org/record/123/files/dataset.zip",
        "https://data.gov/dataset/cancer-stats.json",
        "https://example.com/download/cancer_data.csv",
        "https://kaggle.com/datasets/user/cancer",
        
        # Should FAIL
        "https://medium.com/article-about-cancer-data",
        "https://towardsdatascience.com/tutorial-on-cancer",
        "https://blog.example.com/cancer-analysis",
        "https://news.example.com/cancer-breakthrough",
        "https://youtube.com/watch?v=123"
    ]
    
    print(f"\n{'='*60}")
    print("URL Classifier Test")
    print(f"{'='*60}\n")
    
    for url in test_urls:
        result = classifier.is_dataset_url(url)
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} | {url}")
    
    print(f"\n{'='*60}")
    filtered = classifier.filter_urls(test_urls)
    print(f"Filtered: {len(test_urls)} -> {len(filtered)} URLs")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    test_url_classifier()
