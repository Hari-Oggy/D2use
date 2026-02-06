"""
Unified Orchestrator (V2) - The Production Brain

Consolidates logic from CLI v2 and old Orchestrator into a SINGLE robust source of truth.

Capabilities:
1. Intelligent Search (LLM expansion + Multi-source)
2. Unified Downloading (HuggingFace + Direct URLs)
3. AI-Driven Processing (Profiling, Cleaning, Splitting)
4. Multi-Format Export
"""

import asyncio
import logging
from typing import List, Optional, Dict, Union
from pathlib import Path
import polars as pl
from pydantic import HttpUrl

from .schemas import DatasetCandidate, SourceType, LicenseInfo
from .search.query_expander import QueryExpander
from .search.multi_source import MultiSourceSearch
from .scraper.crawlee_engine import CrawleeEngine
from .processing.compliance_scorer import ComplianceScorer
from .processing.stream_downloader import StreamDownloader
from .analysis.profiler import DatasetProfiler
from .analysis.ai_decision import AIDecisionMaker
from .export.auto_cleaner import AutoCleaner
from .export.split_strategy import DataSplitter
from .export.format_converter import FormatConverter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrchestratorV2:
    """
    The Single Source of Truth for the ML Dataset Factory.
    Used by both CLI and FastAPI.
    """
    
    def __init__(
        self,
        output_dir: Path = Path("output"),
        cache_dir: Path = Path(".cache"),
        use_local_llm: bool = True
    ):
        self.output_dir = output_dir
        self.cache_dir = cache_dir
        self.use_local_llm = use_local_llm
        
        # Ensure dirs exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Components
        self.query_expander = QueryExpander(use_local_llm=use_local_llm)
        self.searcher = MultiSourceSearch()
        self.scorer = ComplianceScorer()
        self.stream_downloader = StreamDownloader() # For direct URLs
        self.scraper = CrawleeEngine() # For web pages
        self.profiler = DatasetProfiler()
        self.ai = AIDecisionMaker(use_local_llm=use_local_llm)
        self.cleaner = AutoCleaner()
        self.splitter = DataSplitter()
        self.converter = FormatConverter(output_dir=output_dir)

    async def intelligent_search(
        self,
        query: str,
        limit: int = 10,
        expand_query: bool = True
    ) -> List[DatasetCandidate]:
        """
        Phase 1: Search with optional LLM expansion.
        """
        logger.info(f"🔍 Searching for: '{query}'")
        
        # 1. Expand query
        queries = [query]
        if expand_query and self.use_local_llm:
            try:
                expanded = await self.query_expander.expand_query(query)
                queries = expanded[:3] # Top 3 variations
                logger.info(f"  Expanded to: {queries}")
            except Exception as e:
                logger.warning(f"  Query expansion failed: {e}")
        
        # 2. Multi-source search
        all_candidates = []
        for q in queries:
            cands = await self.searcher.search_all(q, limit=limit)
            all_candidates.extend(cands)
            if len(all_candidates) >= limit * 2:
                break
        
        # 3. Deduplicate
        seen = set()
        unique_candidates = []
        for c in all_candidates:
            if c.source_id not in seen:
                seen.add(c.source_id)
                unique_candidates.append(c)
        
        # 4. Filter Non-ML (Security, etc.)
        blacklist = ["cwe", "cve", "sast", "security", "benchmark", "vulnerability"]
        ml_candidates = [
            c for c in unique_candidates
            if not any(pattern in c.source_id.lower() for pattern in blacklist)
        ]
        
        # 5. Score
        for c in ml_candidates:
            c.compliance_score = self.scorer.calculate_score(c)
            
        # 6. Sort
        ml_candidates.sort(key=lambda x: x.compliance_score, reverse=True)
        
        logger.info(f"✅ Found {len(ml_candidates)} ML-relevant candidates")
        return ml_candidates[:limit]

    async def process_dataset(
        self,
        candidate_or_id: Union[DatasetCandidate, str],
        dataset_name: str,
        max_rows: int = 1000,
        formats: List[str] = ["jsonl", "parquet", "csv"]
    ) -> Optional[Dict]:
        """
        Phase 2-5: Download -> Clean -> Split -> Export
        """
        logger.info(f"📦 Processing dataset: {dataset_name}")
        
        # Resolve input to candidate if string
        if isinstance(candidate_or_id, str):
            # Auto-detect Kaggle vs HuggingFace based on format
            if "/" in candidate_or_id and not candidate_or_id.startswith("http"):
                # Likely Kaggle: "username/dataset-name"
                 candidate = DatasetCandidate(
                    source_id=candidate_or_id,
                    url=HttpUrl(f"https://www.kaggle.com/datasets/{candidate_or_id}"),
                    source_type=SourceType.KAGGLE,
                    is_downloadable=True,
                    file_metadata={"size_mb": 0, "file_extension": "xlsx"},
                    compliance_score=0.5
                )
            else:
                # Assume HuggingFace
                 candidate = DatasetCandidate(
                    source_id=candidate_or_id,
                    url=HttpUrl(f"https://huggingface.co/datasets/{candidate_or_id}"),
                    source_type=SourceType.HUGGINGFACE,
                    is_downloadable=True,
                    file_metadata={"size_mb": 0, "file_extension": "parquet"},
                    compliance_score=0.5
                )
        else:
            candidate = candidate_or_id

        # 1. Universal Download
        df = await self._universal_download(candidate, max_rows)
        # CRITICAL FIX: Ensure we have data
        if df is None or len(df) == 0:
            logger.error(f"❌ Download failed or empty for {dataset_name}")
            return None
            
        logger.info(f"✅ Downloaded {len(df)} rows.")

        # 2. Profile
        try:
            profile = self.profiler.generate_profile(df)
        except Exception as e:
            logger.error(f"Profiling failed: {e}")
            profile = {"columns": {}, "dataset_info": {"total_rows": len(df)}}
        
        # 3. AI Recipe
        recipe = await self.ai.get_cleaning_recipe(profile)
        
        # 4. Clean
        df_cleaned = self.cleaner.apply_recipe(df.lazy(), recipe, profile).collect()
        
        # 5. Split
        strategy = self.splitter.auto_detect_strategy(df_cleaned, profile, recipe.target_column)
        train, test, val = self.splitter.split(
            df_cleaned,
            strategy=strategy,
            target_column=recipe.target_column
        )
        
        # 6. Export
        # Update converter output dir based on dataset name
        converter = FormatConverter(output_dir=self.output_dir / dataset_name)
        export_paths = converter.export_split(train, test, val, "ml_ready", formats)
        
        result = {
            "dataset_name": dataset_name,
            "original_rows": len(df),
            "cleaned_rows": len(df_cleaned),
            "train_rows": len(train),
            "test_rows": len(test),
            "val_rows": len(val) if val else 0,
            "export_paths": export_paths,
            "strategies": {
                "cleaning": recipe.impute_strategy,
                "splitting": strategy
            }
        }
        
        logger.info(f"🎉 Process Complete: {result['train_rows']} training samples generated.")
        return result

    async def _universal_download(self, candidate: DatasetCandidate, max_rows: int) -> Optional[pl.DataFrame]:
        """
        Smart downloader that handles HuggingFace, Kaggle, and Direct URLs.
        """
        try:
            if candidate.source_type == SourceType.HUGGINGFACE:
                return await self._download_hf(candidate.source_id, max_rows)
            elif candidate.source_type == SourceType.KAGGLE:
                return await self._download_kaggle(candidate.source_id, max_rows)
            elif candidate.source_type == SourceType.WEB_SCRAPE:
                 return await self._download_scraped(str(candidate.url), max_rows)
            else:
                # Fallback: Try HF first, then direct
                df = await self._download_hf(candidate.source_id, max_rows)
                if df is not None: return df
                return await self._download_direct(str(candidate.url), max_rows)
                
        except Exception as e:
            logger.error(f"Universal download failed: {e}")
            return None

    async def _download_hf(self, dataset_id: str, max_rows: int) -> Optional[pl.DataFrame]:
        """Download via HuggingFace datasets library with Robust Failure Handling"""
        logger.info(f"⬇️  Downloading from HuggingFace: {dataset_id}")
        try:
            from datasets import load_dataset, get_dataset_config_names
            
            # Strategy 1: Try to look up configs first (for complex datasets)
            configs = []
            try:
                configs = get_dataset_config_names(dataset_id, trust_remote_code=True)
            except Exception:
                pass
            
            # If configs exist, try the first meaningful one
            target_configs = configs if configs else [None]
            
            # Strategy 2: Try standard splits for each config
            splits_to_try = ["train", "data", "train_test_val", "validation", "test"]
            
            for config in target_configs:
                for split in splits_to_try:
                    try:
                        logger.info(f"  Attempting load: config='{config}', split='{split}'")
                        hf_dataset = load_dataset(
                            dataset_id, 
                            name=config, 
                            split=split, 
                            trust_remote_code=True,
                            streaming=True # Use streaming to check existence quickly
                        )
                        
                        # Take head
                        data_list = list(hf_dataset.take(max_rows))
                        if len(data_list) > 0:
                            logger.info(f"  ✅ Success! Loaded {len(data_list)} rows.")
                            df = pl.DataFrame(data_list)
                            return df
                            
                    except Exception:
                        continue
            
            # Strategy 3: "Empty" load (auto-resolve)
            if not configs:
                try:
                    logger.info("  Attempting generic load...")
                    hf_dataset = load_dataset(dataset_id, trust_remote_code=True, split="train")
                    df = pl.from_arrow(hf_dataset.data.table)
                    if len(df) > max_rows:
                        df = df.head(max_rows)
                    return df
                except Exception:
                    pass

        except Exception as e:
            logger.warning(f"HuggingFace download error: {e}")
        
        return None

    async def _download_kaggle(self, dataset_id: str, max_rows: int) -> Optional[pl.DataFrame]:
        """Download from Kaggle with support for CSV, Parquet, and Excel files"""
        logger.info(f"⬇️  Downloading from Kaggle: {dataset_id}")
        import kaggle
        try:
            # Download to temp location
            download_path = self.output_dir / "_kaggle_tmp" / dataset_id.replace("/", "_")
            download_path.mkdir(parents=True, exist_ok=True)
            
            kaggle.api.dataset_download_files(dataset_id, path=str(download_path), unzip=True)
            
            # Find data files (CSV, Parquet, or Excel)
            files = list(download_path.glob("*"))
            data_files = [
                f for f in files 
                if f.suffix.lower() in ['.csv', '.parquet', '.xlsx', '.xls', '.json', '.jsonl']
            ]
            
            if not data_files:
                logger.warning(f"No data files found in {download_path}")
                return None
            
            # Use the first data file
            file_path = data_files[0]
            logger.info(f"  Loading file: {file_path.name} ({file_path.suffix})")
            
            # Validate downloaded file integrity
            from src.utils.download_validator import validate_download
            if not validate_download(file_path):
                logger.warning("File validation failed, attempting to proceed anyway")
            
            # Load based on file type
            df = None
            if file_path.suffix.lower() == '.csv':
                # Use encoding detection for robust CSV reading
                from src.processing.encoding_detector import read_csv_robust
                df = read_csv_robust(file_path)
            elif file_path.suffix.lower() == '.parquet':
                df = pl.read_parquet(file_path)
            elif file_path.suffix.lower() in ['.xlsx', '.xls']:
                # Excel support using Polars (requires openpyxl)
                logger.info(f"  Reading Excel file...")
                df = pl.read_excel(file_path)
            elif file_path.suffix.lower() == '.jsonl':
                df = pl.read_ndjson(file_path)
            elif file_path.suffix.lower() == '.json':
                df = pl.read_json(file_path)
            else:
                logger.error(f"Unsupported file type: {file_path.suffix}")
                return None
            
            if df is None:
                return None
            
            logger.info(f"  ✅ Success! Loaded {len(df)} rows from Kaggle.")
            
            # Truncate to max_rows
            if len(df) > max_rows:
                df = df.head(max_rows)
            
            return df
            
        except Exception as e:
            logger.error(f"Kaggle download/load failed: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None

    async def _download_scraped(self, url: str, max_rows: int) -> Optional[pl.DataFrame]:
        """Download from a scraped web page"""
        logger.info(f"🕸️  Scraping page for data: {url}")
        
        # 1. Scrape the page
        scraped_data = await self.scraper.scrape_url(url)
        if not scraped_data:
            logger.warning("Scraping returned no data")
            return None
            
        # 2. Find download links
        links = scraped_data.get("download_links", [])
        if not links:
            logger.warning("No download links found on page")
            return None
            
        logger.info(f"  Found {len(links)} potential download links")
        
        # 3. Prioritize formats (Parquet > CSV > JSON)
        priority_extensions = ['.parquet', '.csv', '.json', '.jsonl', '.zip']
        
        sorted_links = []
        for ext in priority_extensions:
            for link in links:
                if link['href'].lower().endswith(ext):
                    sorted_links.append(link)
        
        # Add remaining links
        for link in links:
            if link not in sorted_links:
                sorted_links.append(link)
                
        # 4. Try to download best link
        for link in sorted_links[:3]: # Try top 3
            download_url = link['href']
            # Handle relative URLs
            if download_url.startswith('/'):
                 # Make absolute (simple version)
                 from urllib.parse import urlparse
                 parsed = urlparse(url)
                 base = f"{parsed.scheme}://{parsed.netloc}"
                 download_url = f"{base}{download_url}"
                 
            logger.info(f"  Attempting download from: {download_url}")
            df = await self._download_direct(download_url, max_rows)
            if df is not None and len(df) > 0:
                logger.info(f"  ✅ Successfully downloaded from scraped link!")
                return df
                
        return None

    async def _download_direct(self, url: str, max_rows: int) -> Optional[pl.DataFrame]:
        """Download via StreamDownloader (for CSV/Parquet URLs)"""
        logger.info(f"⬇️  Downloading direct URL: {url}")
        tmp_path = self.cache_dir / "temp_download.file"
        try:
            file_path = await self.stream_downloader.download_chunked(url, tmp_path)
            if not file_path: return None
            
            # Try to read based on extension or content
            if str(file_path).endswith('.parquet'):
                df = pl.read_parquet(file_path)
            elif str(file_path).endswith('.jsonl'):
                df = pl.read_ndjson(file_path)
            else:
                # Default to CSV
                df = pl.read_csv(file_path, ignore_errors=True)
                
            if len(df) > max_rows:
                df = df.head(max_rows)
            return df
        except Exception as e:
            logger.warning(f"Direct download error: {e}")
        return None

    async def close(self):
        await self.ai.close()
