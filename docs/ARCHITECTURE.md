# Architecture Overview

This document provides a visual overview of the ML Dataset Factory architecture.

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          ML DATASET FACTORY                                   │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│   ┌─────────────┐       ┌─────────────────┐       ┌─────────────────┐       │
│   │   CLI v2    │       │    REST API     │       │   Future: UI    │       │
│   │ cli_v2.py   │       │  api/main.py    │       │                 │       │
│   └──────┬──────┘       └────────┬────────┘       └─────────────────┘       │
│          │                       │                                           │
│          └───────────┬───────────┘                                           │
│                      ▼                                                        │
│   ┌──────────────────────────────────────────────────────────────────┐      │
│   │                      ORCHESTRATOR V2                              │      │
│   │                  (orchestrator_v2.py)                            │      │
│   │                                                                   │      │
│   │   • Coordinates all pipeline stages                              │      │
│   │   • Manages data flow                                            │      │
│   │   • Handles errors and retries                                   │      │
│   └──────────────────────────────────────────────────────────────────┘      │
│                                    │                                          │
│          ┌─────────────────────────┼─────────────────────────┐               │
│          ▼                         ▼                         ▼               │
│   ┌─────────────┐          ┌─────────────┐          ┌─────────────┐         │
│   │   SEARCH    │          │  PROCESSING │          │   EXPORT    │         │
│   │   MODULE    │          │   MODULE    │          │   MODULE    │         │
│   └─────────────┘          └─────────────┘          └─────────────┘         │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘


```

---

## Search Module

```
┌─────────────────────────────────────────────────────────────────┐
│                        SEARCH MODULE                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   User Query: "housing prices"                                  │
│         │                                                        │
│         ▼                                                        │
│   ┌─────────────────────────────────────┐                       │
│   │     LLM Query Expansion             │                       │
│   │     (query_expander.py)             │                       │
│   │                                     │                       │
│   │  Input:  "housing prices"           │                       │
│   │  Output: ["real estate prices",     │                       │
│   │           "home values",            │                       │
│   │           "property market data"]   │                       │
│   └──────────────────┬──────────────────┘                       │
│                      │                                           │
│                      ▼                                           │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │              MULTI-SOURCE SEARCH                         │   │
│   │              (multi_source.py)                          │   │
│   ├─────────────────────────────────────────────────────────┤   │
│   │                                                          │   │
│   │   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │   │
│   │   │  Kaggle  │  │   Hugging│  │  SerpAPI │  │   Web   │ │   │
│   │   │  Adapter │  │   Face   │  │  Client  │  │ Scraper │ │   │
│   │   └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘ │   │
│   │        │             │             │             │       │   │
│   │        └──────┬──────┴──────┬──────┴──────┬──────┘       │   │
│   │               │             │             │              │   │
│   │               ▼             ▼             ▼              │   │
│   │         [Candidate 1] [Candidate 2] [Candidate 3]        │   │
│   │                                                          │   │
│   └─────────────────────────────────────────────────────────┘   │
│                      │                                           │
│                      ▼                                           │
│   ┌─────────────────────────────────────┐                       │
│   │     Compliance Scoring              │                       │
│   │     (compliance_scorer.py)          │                       │
│   │                                     │                       │
│   │  • License compatibility: +0.3      │                       │
│   │  • Format support: +0.2             │                       │
│   │  • Size within limits: +0.2         │                       │
│   │  • Quality indicators: +0.3         │                       │
│   └──────────────────┬──────────────────┘                       │
│                      │                                           │
│                      ▼                                           │
│              Best Candidate Selected                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Processing Module

```
┌─────────────────────────────────────────────────────────────────┐
│                      PROCESSING MODULE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Downloaded File                                                │
│         │                                                        │
│         ▼                                                        │
│   ┌─────────────────────────────────────┐                       │
│   │     Encoding Detection              │                       │
│   │     (encoding_detector.py)          │                       │
│   │                                     │                       │
│   │  Supports: UTF-8, Latin-1,          │                       │
│   │  GB18030, Shift_JIS, EUC-KR, etc.   │                       │
│   └──────────────────┬──────────────────┘                       │
│                      │                                           │
│                      ▼                                           │
│   ┌─────────────────────────────────────┐                       │
│   │     File Validation                 │                       │
│   │     (download_validator.py)         │                       │
│   │                                     │                       │
│   │  • CSV structure check              │                       │
│   │  • ZIP integrity test               │                       │
│   │  • Parquet magic bytes              │                       │
│   │  • ZIP bomb detection               │                       │
│   └──────────────────┬──────────────────┘                       │
│                      │                                           │
│                      ▼                                           │
│   ┌─────────────────────────────────────┐                       │
│   │     Dataset Profiling               │                       │
│   │     (profiler.py)                   │                       │
│   │                                     │                       │
│   │  • Column types                     │                       │
│   │  • Missing value %                  │                       │
│   │  • Unique values                    │                       │
│   │  • Statistical summaries            │                       │
│   └──────────────────┬──────────────────┘                       │
│                      │                                           │
│                      ▼                                           │
│   ┌─────────────────────────────────────┐                       │
│   │     AI Decision Making              │  ◄─── LM Studio      │
│   │     (ai_decision.py)                │       (Local LLM)    │
│   │                                     │                       │
│   │  LLM Recommends:                    │                       │
│   │  • Columns to drop                  │                       │
│   │  • Missing value strategy           │                       │
│   │  • Outlier handling                 │                       │
│   └──────────────────┬──────────────────┘                       │
│                      │                                           │
│                      ▼                                           │
│   ┌─────────────────────────────────────┐                       │
│   │     Smart Preprocessing             │                       │
│   │     (auto_cleaner.py)               │                       │
│   │                                     │                       │
│   │  • Date parsing (16 formats)        │                       │
│   │  • Type coercion                    │                       │
│   │  • BOM removal                      │                       │
│   │  • Number formatting                │                       │
│   └──────────────────┬──────────────────┘                       │
│                      │                                           │
│                      ▼                                           │
│              Cleaned DataFrame                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Export Module

```
┌─────────────────────────────────────────────────────────────────┐
│                        EXPORT MODULE                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Cleaned DataFrame                                              │
│         │                                                        │
│         ▼                                                        │
│   ┌─────────────────────────────────────┐                       │
│   │     Data Splitting                  │                       │
│   │     (split_strategy.py)             │                       │
│   │                                     │                       │
│   │  Strategies:                        │                       │
│   │  • Random (default)                 │                       │
│   │  • Stratified (for classification) │                       │
│   │  • Temporal (for time series)       │                       │
│   │                                     │                       │
│   │  Ratios: 80% train, 10% val, 10% test│                      │
│   └──────────────────┬──────────────────┘                       │
│                      │                                           │
│         ┌────────────┼────────────┐                             │
│         ▼            ▼            ▼                             │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐                       │
│   │  Train   │ │   Val    │ │   Test   │                       │
│   │  80%     │ │   10%    │ │   10%    │                       │
│   └────┬─────┘ └────┬─────┘ └────┬─────┘                       │
│        │            │            │                              │
│        └────────────┼────────────┘                              │
│                     ▼                                            │
│   ┌─────────────────────────────────────┐                       │
│   │     Format Conversion               │                       │
│   │     (format_converter.py)           │                       │
│   └──────────────────┬──────────────────┘                       │
│                      │                                           │
│         ┌────────────┼────────────┐                             │
│         ▼            ▼            ▼                             │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐                       │
│   │   CSV    │ │ Parquet  │ │  JSONL   │                       │
│   │          │ │          │ │          │                       │
│   └──────────┘ └──────────┘ └──────────┘                       │
│                                                                  │
│   Output Structure:                                              │
│   output/cli_v2/<dataset>/                                      │
│   ├── ml_ready_train.csv                                        │
│   ├── ml_ready_train.parquet                                    │
│   ├── ml_ready_train.jsonl                                      │
│   ├── ml_ready_test.csv                                         │
│   └── ml_ready_val.csv                                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Retry & Resilience

```
┌─────────────────────────────────────────────────────────────────┐
│                    RETRY & RESILIENCE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   API Request                                                    │
│         │                                                        │
│         ▼                                                        │
│   ┌─────────────────────────────────────┐                       │
│   │     @retry_api_call decorator       │                       │
│   │     (retry.py)                      │                       │
│   │                                     │                       │
│   │  Config:                            │                       │
│   │  • max_attempts: 3                  │                       │
│   │  • base_delay: 1.0s                 │                       │
│   │  • max_delay: 30.0s                 │                       │
│   │  • jitter: 0.1                      │                       │
│   └──────────────────┬──────────────────┘                       │
│                      │                                           │
│          ┌───────────┴───────────┐                              │
│          ▼                       ▼                              │
│    [Success]            [Retry Error (429, 503)]                │
│         │                       │                               │
│         │               ┌───────▼───────┐                       │
│         │               │ Exponential   │                       │
│         │               │ Backoff       │                       │
│         │               │               │                       │
│         │               │ delay = min(  │                       │
│         │               │   base * 2^n, │                       │
│         │               │   max_delay   │                       │
│         │               │ ) + jitter    │                       │
│         │               └───────┬───────┘                       │
│         │                       │                               │
│         │                       ▼                               │
│         │               [Retry Request]                         │
│         │                       │                               │
│         └───────────────────────┘                               │
│                                                                  │
│   Timeline Example:                                              │
│   ──────────────────────────────────────────────────►           │
│   │ Req │ Fail │ 1s │ Retry │ Fail │ 2s │ Retry │ OK │         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

| Layer               | Technology   | Purpose                   |
| ------------------- | ------------ | ------------------------- |
| **Language**        | Python 3.11+ | Core runtime              |
| **Data Processing** | Polars       | Fast DataFrame operations |
| **API Framework**   | FastAPI      | REST API server           |
| **AI/LLM**          | LM Studio    | Local AI inference        |
| **Web Scraping**    | Playwright   | Browser automation        |
| **HTTP Client**     | httpx        | Async HTTP requests       |
| **Validation**      | Pydantic     | Data validation           |
| **Package Manager** | uv           | Dependency management     |

---

_Architecture documentation - ML Dataset Factory v1.0.0_
