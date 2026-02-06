# 🚀 Getting Started Guide

> **Complete setup instructions for ML Dataset Factory**

This guide will get you from zero to running in under 10 minutes.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [LM Studio Setup (AI Features)](#lm-studio-setup)
4. [API Keys Configuration](#api-keys-configuration)
5. [Running the Project](#running-the-project)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

| Software  | Version | Download                                        |
| --------- | ------- | ----------------------------------------------- |
| Python    | 3.11+   | [python.org](https://www.python.org/downloads/) |
| uv        | Latest  | [astral.sh/uv](https://github.com/astral-sh/uv) |
| LM Studio | Latest  | [lmstudio.ai](https://lmstudio.ai/)             |
| Git       | Latest  | [git-scm.com](https://git-scm.com/)             |

### System Requirements

- **Minimum**: 8GB RAM, 10GB disk space
- **Recommended**: 16GB RAM, 20GB disk (for AI models)

---

## Installation

### Step 1: Clone the Repository

```bash
git clone <your-repo-url>
cd D2use
```

### Step 2: Install uv (if not installed)

**Windows (PowerShell)**:

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Linux/Mac**:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Step 3: Install Dependencies

```bash
uv sync
```

This installs all Python packages automatically.

### Step 4: Create Environment File

```bash
cp .env.example .env
```

Edit `.env` with your API keys (see [API Keys Configuration](#api-keys-configuration)).

---

## LM Studio Setup

LM Studio provides the AI brain for intelligent data cleaning. Follow these steps:

### Step 1: Download LM Studio

1. Go to [https://lmstudio.ai/](https://lmstudio.ai/)
2. Download for your OS (Windows/Mac/Linux)
3. Install and launch

### Step 2: Download a Model

**Recommended Models** (in order of preference):

| Model                    | Size  | Speed     | Quality   | Best For       |
| ------------------------ | ----- | --------- | --------- | -------------- |
| **Qwen 2.5 7B Instruct** | 4.7GB | Fast      | Excellent | ✅ Recommended |
| Llama 3.2 3B             | 2GB   | Fastest   | Good      | Low-end PCs    |
| Mistral 7B               | 4.1GB | Fast      | Excellent | Alternative    |
| Phi-3 Mini               | 2.3GB | Very Fast | Good      | Quick tests    |

**How to Download**:

1. In LM Studio, click the **Search/Download** icon (magnifying glass) on the left
2. Search: `qwen2.5-7b-instruct`
3. Find: **Qwen/Qwen2.5-7B-Instruct-GGUF**
4. Click the download button next to: `qwen2.5-7b-instruct-q4_k_m.gguf`
5. Wait for download (4.7GB)

![Download Model](../assets/lmstudio-download.png)

### Step 3: Load the Model

1. Click **Local Server** tab (left sidebar - looks like `<>`)
2. Click the dropdown at the top to select your model
3. Select `qwen2.5-7b-instruct-q4_k_m`
4. Wait for model to load (may take 30-60 seconds)

### Step 4: Start the Server

1. Click **Start Server** button
2. Wait until status shows: `Running on http://localhost:1234`
3. The server indicator should turn green

### Step 5: Verify Connection

Open a terminal and run:

```bash
curl http://localhost:1234/v1/models
```

You should see:

```json
{"data": [{"id": "qwen2.5-7b-instruct", ...}]}
```

**✅ LM Studio is now ready!**

---

## API Keys Configuration

You need API keys from 3 services (all free tiers available):

### 1. Kaggle API Key (Required)

1. Go to [kaggle.com/settings/account](https://www.kaggle.com/settings/account)
2. Scroll to **API** section
3. Click **Create New API Token**
4. Download `kaggle.json`
5. Copy the values to `.env`:

```bash
KAGGLE_USERNAME=your_kaggle_username
KAGGLE_KEY=your_kaggle_api_key
```

### 2. HuggingFace Token (Required)

1. Go to [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
2. Click **New token**
3. Name: `ml-dataset-factory`
4. Role: **Read**
5. Click **Generate**
6. Copy to `.env`:

```bash
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 3. SerpAPI Key (Optional - for web search)

1. Go to [serpapi.com](https://serpapi.com/)
2. Sign up (100 free searches/month)
3. Copy API key to `.env`:

```bash
SERPAPI_KEY=xxxxxxxxxxxxxxxxxx
```

### Complete `.env` Example

```bash
# ===========================================
# ML Dataset Factory - Configuration
# ===========================================

# --- API Keys (Required) ---
KAGGLE_USERNAME=your_username
KAGGLE_KEY=your_api_key
HF_TOKEN=hf_your_token_here

# --- API Keys (Optional) ---
SERPAPI_KEY=your_serpapi_key  # 100 free/month
GEMINI_API_KEY=               # Optional: Google Gemini

# --- LM Studio Settings ---
USE_LOCAL_LLM=true
LLM_MODEL=qwen2.5-7b-instruct
LLM_ENDPOINT=http://localhost:1234/v1/chat/completions
LLM_TEMPERATURE=0.2
LLM_TIMEOUT=120
LLM_MAX_TOKENS=2000

# --- Processing Limits ---
MAX_FILE_SIZE_MB=500
MAX_DATASET_ROWS=10000

# --- Output Settings ---
OUTPUT_DIR=output
CACHE_DIR=.cache
```

---

## Running the Project

### Option 1: CLI (Command Line)

**Basic usage:**

```bash
uv run python -m src.cli_v2 "your search query" --max-rows 1000
```

**Examples:**

```bash
# Find and process housing data
uv run python -m src.cli_v2 "housing prices" --max-rows 2000

# Credit card fraud detection data
uv run python -m src.cli_v2 "credit card fraud" --max-rows 5000

# Specific Kaggle dataset
uv run python -m src.cli_v2 "mlg-ulb/creditcardfraud" --max-rows 10000
```

**Output:**

Files are saved to `output/cli_v2/<dataset_name>/`:

```
output/
└── cli_v2/
    └── housing_prices_best/
        ├── ml_ready_train.csv
        ├── ml_ready_test.csv
        ├── ml_ready_val.csv
        ├── ml_ready_train.parquet
        └── ml_ready_train.jsonl
```

### Option 2: REST API

**Start the server:**

```bash
uv run python -m src.api.main
```

Server runs at: `http://localhost:8000`

**API Endpoints:**

| Method | Endpoint   | Description         |
| ------ | ---------- | ------------------- |
| GET    | `/health`  | Health check        |
| POST   | `/search`  | Search for datasets |
| POST   | `/process` | Process a dataset   |

**Example: Search**

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "customer churn", "limit": 5}'
```

**Example: Process**

```bash
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"dataset_name": "mlg-ulb/creditcardfraud", "max_rows": 5000}'
```

---

## Troubleshooting

### Issue: "LM Studio connection failed"

**Solution:**

1. Check LM Studio is running (green indicator)
2. Verify model is loaded
3. Check server is started on port 1234
4. Test: `curl http://localhost:1234/v1/models`

### Issue: "Kaggle authentication failed"

**Solution:**

1. Verify `KAGGLE_USERNAME` and `KAGGLE_KEY` in `.env`
2. Or place `kaggle.json` in `~/.kaggle/` folder
3. On Windows: `C:\Users\<username>\.kaggle\kaggle.json`

### Issue: "HuggingFace rate limit"

**Solution:**

1. Wait 1-2 minutes (rate limits reset)
2. Add valid `HF_TOKEN` to `.env`

### Issue: "Out of memory"

**Solution:**

1. Reduce dataset size: `--max-rows 1000`
2. Close LM Studio temporarily
3. Use a smaller model (Phi-3 Mini)

### Issue: "Excel file not loading"

**Solution:**

```bash
uv add openpyxl fastexcel
```

---

## Quick Reference

### CLI Commands

```bash
# Basic search and process
uv run python -m src.cli_v2 "query" --max-rows 1000

# Without AI (faster, basic cleaning)
USE_LOCAL_LLM=false uv run python -m src.cli_v2 "query"

# Run tests
uv run pytest tests/ -v
```

### Key Files

| File                     | Purpose                    |
| ------------------------ | -------------------------- |
| `.env`                   | API keys and configuration |
| `src/cli_v2.py`          | Command-line interface     |
| `src/api/main.py`        | REST API server            |
| `src/orchestrator_v2.py` | Main pipeline logic        |
| `src/config.py`          | Configuration settings     |

---

## Next Steps

Once setup is complete:

1. ✅ Run a test: `uv run python -m src.cli_v2 "iris" --max-rows 500`
2. ✅ Check output in `output/cli_v2/`
3. ✅ Try different queries with your domain data

**Need help?** Check the [Troubleshooting](#troubleshooting) section or open an issue.

---

**Happy data processing! 🎉**
