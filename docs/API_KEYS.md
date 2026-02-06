# 🔧 API Keys & Configuration Guide

> **How to obtain and configure all required API keys**

---

## Overview

| Service         | Required?   | Free Tier | Purpose                   |
| --------------- | ----------- | --------- | ------------------------- |
| **Kaggle**      | ✅ Yes      | Unlimited | Download datasets         |
| **HuggingFace** | ✅ Yes      | Unlimited | Access ML datasets        |
| **SerpAPI**     | ⚪ Optional | 100/month | Web search for datasets   |
| **Gemini**      | ⚪ Optional | Free tier | Alternative AI (not used) |

---

## 1. Kaggle API Key (Required)

Kaggle hosts thousands of ML datasets that this tool can access.

### Get Your Kaggle API Key

1. Go to [kaggle.com](https://www.kaggle.com/)
2. Sign up or log in
3. Click your profile picture → **Settings**
4. Scroll to **API** section
5. Click **Create New API Token**
6. A file `kaggle.json` will download

### The kaggle.json File

```json
{
  "username": "your_username",
  "key": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
```

### Configure in .env

Add to your `.env` file:

```bash
KAGGLE_USERNAME=your_username
KAGGLE_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Alternative: Place kaggle.json

Instead of `.env`, you can place the file directly:

- **Windows**: `C:\Users\<YourName>\.kaggle\kaggle.json`
- **Linux/Mac**: `~/.kaggle/kaggle.json`

Make sure the file has restricted permissions:

```bash
chmod 600 ~/.kaggle/kaggle.json
```

---

## 2. HuggingFace Token (Required)

HuggingFace hosts ML datasets and models.

### Get Your HuggingFace Token

1. Go to [huggingface.co](https://huggingface.co/)
2. Sign up or log in
3. Click your profile → **Settings**
4. Click **Access Tokens** (left sidebar)
5. Click **New token**
6. Configure:
   - Name: `ml-dataset-factory` (or anything)
   - Role: **Read**
7. Click **Generate token**
8. Copy the token (starts with `hf_`)

### Configure in .env

```bash
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 3. SerpAPI Key (Optional)

SerpAPI enables web search to find datasets from various sources.

### Get Your SerpAPI Key

1. Go to [serpapi.com](https://serpapi.com/)
2. Sign up (free tier: 100 searches/month)
3. Go to Dashboard
4. Copy your API Key

### Configure in .env

```bash
SERPAPI_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### If Not Configured

Without SerpAPI:

- ✅ Kaggle search works
- ✅ HuggingFace search works
- ❌ Web search disabled (minor feature)

---

## Complete .env Template

Create a file named `.env` in the project root:

```bash
# ===========================================
# ML Dataset Factory - Configuration
# ===========================================

# =============== API KEYS ===============

# Kaggle API (Required)
# Get from: https://www.kaggle.com/settings/account
KAGGLE_USERNAME=your_kaggle_username
KAGGLE_KEY=your_kaggle_api_key_here

# HuggingFace Token (Required)
# Get from: https://huggingface.co/settings/tokens
HF_TOKEN=hf_your_huggingface_token_here

# SerpAPI Key (Optional - for web search)
# Get from: https://serpapi.com/
SERPAPI_KEY=your_serpapi_key_here

# Gemini API Key (Optional - not used currently)
GEMINI_API_KEY=

# =============== LM STUDIO ===============

# Enable/disable local AI
USE_LOCAL_LLM=true

# Model configuration
LLM_MODEL=qwen2.5-7b-instruct
LLM_ENDPOINT=http://localhost:1234/v1/chat/completions
LLM_TEMPERATURE=0.2
LLM_TIMEOUT=120
LLM_MAX_TOKENS=2000

# =============== LIMITS ===============

# Maximum file size to download (MB)
MAX_FILE_SIZE_MB=500

# Maximum rows to process
MAX_DATASET_ROWS=10000

# =============== PATHS ===============

# Output directory for processed datasets
OUTPUT_DIR=output

# Cache directory for downloads
CACHE_DIR=.cache
```

---

## Verify Configuration

Run this command to check your configuration:

```bash
uv run python -c "from src.config import settings; print('✅ Config loaded'); print(f'Kaggle: {settings.KAGGLE_USERNAME}'); print(f'HF Token: {settings.HF_TOKEN[:10]}...')"
```

**Expected output:**

```
✅ Config loaded
Kaggle: your_username
HF Token: hf_xxxxxxx...
```

---

## Security Notes

⚠️ **Never commit .env to git!**

The `.gitignore` already includes `.env`, but double-check:

```bash
# In .gitignore
.env
kaggle.json
```

⚠️ **Don't share your API keys!**

If you accidentally expose a key:

1. Go to the respective service
2. Revoke/delete the old key
3. Generate a new one
4. Update your `.env`

---

## Troubleshooting

### "Kaggle API authentication failed"

```
kaggle.rest.ApiException: 401 - Unauthorized
```

**Solutions:**

1. Verify username and key are correct
2. Check for extra spaces in `.env`
3. Try placing `kaggle.json` in `~/.kaggle/`

### "HuggingFace 401 Unauthorized"

**Solutions:**

1. Verify token starts with `hf_`
2. Check token has "Read" permissions
3. Try generating a new token

### "SerpAPI quota exceeded"

```
SerpAPI: Over monthly search limit
```

**Solutions:**

1. Wait for monthly reset
2. Upgrade to paid plan
3. Or just skip - web search is optional

---


