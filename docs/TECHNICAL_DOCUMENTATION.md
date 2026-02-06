# ML Dataset Factory - Technical Documentation

> **Version 1.0.0** | Last Updated: January 2026

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [Installation](#3-installation)
4. [Configuration](#4-configuration)
5. [API Reference](#5-api-reference)
6. [CLI Reference](#6-cli-reference)
7. [Data Flow](#7-data-flow)
8. [Robustness Features](#8-robustness-features)
9. [Testing](#9-testing)
10. [Deployment](#10-deployment)
11. [Troubleshooting](#11-troubleshooting)
12. [Contributing](#12-contributing)
13. [Changelog](#13-changelog)

---

## 1. Overview

### 1.1 What is ML Dataset Factory?

ML Dataset Factory is a production-grade automated pipeline that transforms raw datasets from multiple sources (Kaggle, HuggingFace, Web) into ML-ready training data.

### 1.2 Key Features

| Feature                     | Description                                                |
| --------------------------- | ---------------------------------------------------------- |
| **Multi-Source Search**     | Kaggle, HuggingFace, SerpAPI, Web Scraping                 |
| **AI-Powered Cleaning**     | Local LLM (LM Studio) makes intelligent cleaning decisions |
| **Automatic Preprocessing** | Encoding detection, date parsing, type coercion            |
| **Smart Splitting**         | Train/test/validation with stratification support          |
| **Multi-Format Export**     | CSV, Parquet, JSONL                                        |
| **Robustness**              | Retry logic, rate limiting, file validation                |

### 1.3 System Requirements

| Component | Minimum | Recommended             |
| --------- | ------- | ----------------------- |
| Python    | 3.11+   | 3.12+                   |
| RAM       | 8GB     | 16GB+                   |
| Disk      | 10GB    | 20GB+                   |
| GPU       | None    | NVIDIA (for faster LLM) |

### 1.4 Technology Stack

- **Language**: Python 3.11+
- **Data Processing**: Polars (fast DataFrame library)
- **API Framework**: FastAPI
- **AI Integration**: LM Studio (local LLM)
- **Web Scraping**: Playwright
- **Package Manager**: uv

---

## 2. Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        ML Dataset Factory                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐           │
│  │   CLI v2    │   │  REST API   │   │  (Future)   │           │
│  │  cli_v2.py  │   │ api/main.py │   │   Web UI    │           │
│  └──────┬──────┘   └──────┬──────┘   └─────────────┘           │
│         │                 │                                      │
│         └────────┬────────┘                                      │
│                  ▼                                               │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Orchestrator V2                         │  │
│  │               (orchestrator_v2.py)                        │  │
│  │  - Search coordination                                     │  │
│  │  - Download management                                     │  │
│  │  - Processing pipeline                                     │  │
│  │  - Export handling                                         │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│         ┌────────────────────┼────────────────────┐             │
│         ▼                    ▼                    ▼             │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │   Search    │     │  Processing │     │   Export    │       │
│  │   Module    │     │   Module    │     │   Module    │       │
│  └─────────────┘     └─────────────┘     └─────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Module Breakdown

```
src/
├── adapters/                 # External API integrations
│   ├── huggingface.py       # HuggingFace Hub API
│   └── kaggle.py            # Kaggle API
│
├── analysis/                 # Data analysis & AI
│   ├── ai_decision.py       # LLM-powered decisions
│   ├── config.py            # Analysis configuration
│   └── profiler.py          # Dataset profiling
│
├── api/                      # REST API
│   ├── main.py              # FastAPI application
│   └── routes/              # API endpoints
│
├── export/                   # Data export
│   ├── auto_cleaner.py      # Automated cleaning
│   ├── format_converter.py  # Format conversion
│   └── split_strategy.py    # Train/test splitting
│
├── processing/               # Data processing
│   ├── compliance_scorer.py # Dataset scoring
│   ├── encoding_detector.py # Encoding detection
│   ├── date_parser.py       # Date format parsing
│   └── stream_downloader.py # File downloading
│
├── scraper/                  # Web scraping
│   ├── circuit_breaker.py   # Request protection
│   ├── crawlee_engine.py    # Playwright scraper
│   └── llm_extractor.py     # AI data extraction
│
├── search/                   # Dataset search
│   ├── multi_source.py      # Unified search
│   ├── query_expander.py    # AI query expansion
│   └── serpapi_client.py    # Google search API
│
├── utils/                    # Utilities
│   ├── download_validator.py # File validation
│   ├── error_messages.py    # User-friendly errors
│   └── retry.py             # Retry logic
│
├── config.py                 # Configuration
├── schemas.py                # Pydantic models
├── cli_v2.py                 # CLI entry point
└── orchestrator_v2.py        # Main orchestrator
```

### 2.3 Data Flow Diagram

```
User Query ("housing prices")
         │
         ▼
┌─────────────────────────────┐
│    Query Expansion (LLM)    │
│ "housing prices" →          │
│ ["real estate", "home       │
│  prices", "housing market"] │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│    Multi-Source Search      │
│ ├─ Kaggle API               │
│ ├─ HuggingFace API          │
│ ├─ SerpAPI (Google)         │
│ └─ Web Scraper              │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│   Compliance Scoring        │
│ Score datasets by:          │
│ - License compatibility     │
│ - File format support       │
│ - Size constraints          │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│       Download              │
│ ├─ Encoding detection       │
│ ├─ File validation          │
│ └─ Retry on failure         │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│    AI Analysis (LLM)        │
│ ├─ Column profiling         │
│ ├─ Drop recommendations     │
│ ├─ Missing value strategy   │
│ └─ Outlier handling         │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│   Smart Preprocessing       │
│ ├─ Date parsing             │
│ ├─ Type coercion            │
│ ├─ BOM removal              │
│ └─ Number formatting        │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│        Cleaning             │
│ ├─ Drop columns             │
│ ├─ Handle missing values    │
│ ├─ Clip outliers            │
│ └─ Strip commas             │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│     Train/Test Split        │
│ ├─ Random (default)         │
│ ├─ Stratified               │
│ └─ Temporal                 │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│       Export                │
│ ├─ CSV                      │
│ ├─ Parquet                  │
│ └─ JSONL                    │
└─────────────────────────────┘
         │
         ▼
    ML-Ready Data
```

---

## 3. Installation

### 3.1 Prerequisites

```bash
# Install Python 3.11+
python --version  # Should be 3.11+

# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3.2 Clone & Install

```bash
# Clone repository
git clone <repository-url>
cd D2use

# Install dependencies
uv sync

# Create configuration
cp .env.example .env
```

### 3.3 Verify Installation

```bash
uv run python -c "from src.config import settings; print('✅ Installation successful')"
```

---

## 4. Configuration

### 4.1 Environment Variables

| Variable           | Required | Default                                     | Description                |
| ------------------ | -------- | ------------------------------------------- | -------------------------- |
| `KAGGLE_USERNAME`  | Yes      | -                                           | Kaggle account username    |
| `KAGGLE_KEY`       | Yes      | -                                           | Kaggle API key             |
| `HF_TOKEN`         | Yes      | -                                           | HuggingFace access token   |
| `SERPAPI_KEY`      | No       | -                                           | SerpAPI key for web search |
| `USE_LOCAL_LLM`    | No       | `true`                                      | Enable AI-powered cleaning |
| `LLM_MODEL`        | No       | `qwen2.5-7b-instruct`                       | Model name                 |
| `LLM_ENDPOINT`     | No       | `http://localhost:1234/v1/chat/completions` | LM Studio URL              |
| `MAX_FILE_SIZE_MB` | No       | `500`                                       | Max download size          |
| `MAX_DATASET_ROWS` | No       | `10000`                                     | Max rows to process        |

### 4.2 Sample .env File

```bash
# API Keys
KAGGLE_USERNAME=your_username
KAGGLE_KEY=your_key
HF_TOKEN=hf_your_token
SERPAPI_KEY=your_serpapi_key

# LM Studio
USE_LOCAL_LLM=true
LLM_MODEL=qwen2.5-7b-instruct
LLM_ENDPOINT=http://localhost:1234/v1/chat/completions
LLM_TEMPERATURE=0.2
LLM_TIMEOUT=120

# Limits
MAX_FILE_SIZE_MB=500
MAX_DATASET_ROWS=10000

# Paths
OUTPUT_DIR=output
CACHE_DIR=.cache
```

---

## 5. API Reference

### 5.1 Start Server

```bash
uv run python -m src.api.main
# Server runs at http://localhost:8000
```

### 5.2 Endpoints

#### GET /health

Health check endpoint.

**Response:**

```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

#### POST /search

Search for datasets.

**Request:**

```json
{
  "query": "customer churn",
  "limit": 5,
  "expand_query": true
}
```

**Response:**

```json
{
  "status": "success",
  "candidates": [
    {
      "source_id": "telco-churn",
      "url": "https://kaggle.com/...",
      "source_type": "KAGGLE",
      "compliance_score": 0.85
    }
  ]
}
```

#### POST /process

Process a specific dataset.

**Request:**

```json
{
  "dataset_name": "mlg-ulb/creditcardfraud",
  "max_rows": 5000,
  "export_formats": ["csv", "parquet"]
}
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "original_rows": 5000,
    "cleaned_rows": 4892,
    "train_rows": 3913,
    "test_rows": 979,
    "export_paths": {
      "train_csv": "output/api/creditcardfraud/ml_ready_train.csv"
    }
  }
}
```

---

## 6. CLI Reference

### 6.1 Basic Usage

```bash
uv run python -m src.cli_v2 "query" [options]
```

### 6.2 Arguments

| Argument | Type   | Description                |
| -------- | ------ | -------------------------- |
| `query`  | string | Search query or dataset ID |

### 6.3 Options

| Option       | Default | Description             |
| ------------ | ------- | ----------------------- |
| `--max-rows` | 5000    | Maximum rows to process |

### 6.4 Examples

```bash
# Basic search
uv run python -m src.cli_v2 "housing prices" --max-rows 1000

# Specific Kaggle dataset
uv run python -m src.cli_v2 "mlg-ulb/creditcardfraud" --max-rows 5000

# Without AI (faster)
USE_LOCAL_LLM=false uv run python -m src.cli_v2 "iris"
```

### 6.5 Output Structure

```
output/cli_v2/<dataset_name>/
├── ml_ready_train.csv
├── ml_ready_test.csv
├── ml_ready_val.csv
├── ml_ready_train.parquet
├── ml_ready_train.jsonl
└── (audit_log.json)
```

---

## 7. Data Flow

### 7.1 Processing Pipeline

1. **Query Expansion**: LLM generates related search terms
2. **Multi-Source Search**: Parallel search across Kaggle, HuggingFace, SerpAPI
3. **Candidate Scoring**: Rank by license, format, size
4. **Download**: With encoding detection and validation
5. **Profiling**: Analyze columns, types, missing values
6. **AI Decision**: LLM recommends cleaning strategy
7. **Preprocessing**: Date parsing, type coercion
8. **Cleaning**: Apply AI recommendations
9. **Splitting**: Train/test/validation sets
10. **Export**: Multiple formats

### 7.2 Supported Formats

| Format              | Read | Write |
| ------------------- | ---- | ----- |
| CSV                 | ✅   | ✅    |
| Parquet             | ✅   | ✅    |
| JSONL               | ✅   | ✅    |
| JSON                | ✅   | ❌    |
| Excel (.xlsx, .xls) | ✅   | ❌    |

---

## 8. Robustness Features

### 8.1 Encoding Detection

Automatically detects and handles 14+ encodings:

- UTF-8, UTF-8 BOM, Latin-1, Windows-1252
- Chinese (GB18030, GBK), Japanese (Shift_JIS), Korean (EUC-KR)

### 8.2 Date Parsing

Auto-detects 16+ date formats:

- ISO: `2024-01-31`
- European: `31/01/2024`
- American: `01/31/2024`
- Unix timestamps

### 8.3 Retry Logic

- Exponential backoff with jitter
- Max 3 attempts for API calls
- Handles 429 rate limiting

### 8.4 File Validation

- Checksum verification
- ZIP bomb detection
- Truncation detection

---

## 9. Testing

### 9.1 Run Tests

```bash
# All tests
uv run pytest tests/ -v

# Specific module
uv run pytest tests/test_encoding_detector.py -v

# With coverage
uv run pytest tests/ --cov=src
```

### 9.2 Test Files

| File                        | Tests   |
| --------------------------- | ------- |
| `test_encoding_detector.py` | 5 tests |
| `test_date_parser.py`       | 8 tests |
| `test_retry.py`             | 6 tests |

---

## 10. Deployment

### 10.1 Development

```bash
# Start API server
uv run python -m src.api.main

# With hot reload
uv run uvicorn src.api.main:app --reload
```

### 10.2 Production

```bash
# Using gunicorn
uv run gunicorn src.api.main:app -w 4 -k uvicorn.workers.UvicornWorker

# With Docker (future)
docker build -t ml-dataset-factory .
docker run -p 8000:8000 ml-dataset-factory
```

---

## 11. Troubleshooting

### 11.1 Common Issues

| Issue                       | Solution                             |
| --------------------------- | ------------------------------------ |
| LM Studio connection failed | Start LM Studio server on port 1234  |
| Kaggle auth failed          | Check KAGGLE_USERNAME and KAGGLE_KEY |
| Out of memory               | Use `--max-rows 1000`                |
| Encoding errors             | Automatic fallback to Latin-1        |

### 11.2 Debug Mode

```bash
# Enable verbose logging
LOG_LEVEL=DEBUG uv run python -m src.cli_v2 "query"
```

---

## 12. Contributing

### 12.1 Development Setup

```bash
git clone <repo>
cd D2use
uv sync --dev
```

### 12.2 Code Style

- Black for formatting
- isort for imports
- Type hints required

### 12.3 Pull Request Process

1. Create feature branch
2. Write tests
3. Update documentation
4. Submit PR

---

## 13. Changelog

### v1.0.0 (January 2026)

**Features:**

- Multi-source dataset search (Kaggle, HuggingFace, SerpAPI)
- AI-powered data cleaning (LM Studio integration)
- Automatic encoding detection (14 encodings)
- Smart date parsing (16 formats)
- Retry logic with exponential backoff
- File integrity validation
- User-friendly error messages

**Tested:**

- 14+ datasets processed successfully
- 19 unit tests passing
- Multiple domain coverage (finance, healthcare, NLP, etc.)

---

## License

MIT License - See [LICENSE](../LICENSE) file.

---

## Support

- **Issues**: GitHub Issues
- **Documentation**: This file + `/docs` folder
- **Email**: Contact maintainers

---

_Documentation generated: January 2026_
