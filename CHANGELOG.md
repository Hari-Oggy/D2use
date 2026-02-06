# Changelog

All notable changes to ML Dataset Factory will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-01-31

### Added

#### Core Features

- **Multi-Source Dataset Search**: Unified search across Kaggle, HuggingFace, SerpAPI, and web scraping
- **AI-Powered Cleaning**: Integration with LM Studio for intelligent data cleaning decisions
- **Smart Query Expansion**: LLM expands search queries for better results
- **Automatic Preprocessing**: Encoding detection, date parsing, type coercion

#### Data Processing

- **Encoding Auto-Detection**: Support for 14+ encodings (UTF-8, Latin-1, Chinese, Japanese, Korean)
- **Smart Date Parsing**: Auto-detection of 16+ date formats
- **Mixed Type Coercion**: Intelligent handling of columns with mixed data types
- **BOM Stripping**: Automatic removal of BOM and zero-width characters
- **Comma Number Handling**: Strip commas from formatted numbers

#### Robustness

- **Retry Logic**: Exponential backoff with jitter for API calls
- **File Validation**: CSV, ZIP, Parquet, JSON, Excel integrity checks
- **ZIP Bomb Detection**: Security protection against decompression attacks
- **User-Friendly Errors**: 17 categorized error types with actionable solutions

#### Export

- **Multi-Format Export**: CSV, Parquet, JSONL
- **Smart Splitting**: Train/test/validation with random, stratified, temporal strategies
- **Excel Support**: Read .xlsx and .xls files

#### API

- **REST API**: FastAPI-based server with /search and /process endpoints
- **CLI Tool**: Command-line interface for quick dataset processing

### Technical Stack

- Python 3.11+
- Polars for data processing
- FastAPI for REST API
- Playwright for web scraping
- LM Studio for local AI

### Testing

- 19 unit tests (100% passing)
- 14+ real dataset validations
- Multi-domain coverage (finance, healthcare, NLP, etc.)

---

## [0.9.0] - 2026-01-30 (Pre-release)

### Added

- Initial HuggingFace and Kaggle adapter implementation
- Basic orchestrator logic
- LM Studio integration prototype

### Changed

- Refactored configuration to use pydantic-settings

---

## Future Roadmap

### [1.1.0] - Planned

- [ ] Dataset caching (prevent re-downloads)
- [ ] Data quality reports (show what was cleaned)
- [ ] Memory streaming for large files (>1GB)

### [1.2.0] - Planned

- [ ] Nested JSON parsing
- [ ] Timezone normalization
- [ ] Observability metrics dashboard
- [ ] Docker support

### [2.0.0] - Future

- [ ] Web UI dashboard
- [ ] Scheduled dataset updates
- [ ] Team collaboration features

---

## Migration Notes

### From 0.x to 1.0

1. Update `.env` file with new variables
2. Install new dependencies: `uv sync`
3. LM Studio is now optional (set `USE_LOCAL_LLM=false` to disable)

---

_Maintained by the ML Dataset Factory team_
