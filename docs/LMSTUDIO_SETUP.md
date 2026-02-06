# 🤖 LM Studio Complete Setup Guide

> **Step-by-step guide to configure LM Studio for ML Dataset Factory**

---

## What is LM Studio?

LM Studio is a free, local application that runs AI language models on your computer. This project uses it for:

- **Intelligent query expansion** (finds better datasets)
- **Data cleaning decisions** (drops useless columns, handles missing values)
- **Schema understanding** (interprets what each column means)

**No internet required** - all AI processing happens locally!

---

## System Requirements

| Component | Minimum                            | Recommended          |
| --------- | ---------------------------------- | -------------------- |
| RAM       | 8GB                                | 16GB+                |
| Disk      | 5GB                                | 10GB+                |
| GPU       | None (CPU works)                   | NVIDIA/AMD for speed |
| OS        | Windows 10, macOS 11, Ubuntu 20.04 | Latest versions      |

---

## Step 1: Download LM Studio

1. Go to **[lmstudio.ai](https://lmstudio.ai/)**
2. Click **Download** for your operating system
3. Install the application

![LM Studio Download](../assets/lmstudio-homepage.png)

---

## Step 2: Launch LM Studio

1. Open LM Studio
2. You'll see the main interface with a chat area

---

## Step 3: Download a Model

### Recommended Model: Qwen 2.5 7B Instruct

This model offers the best balance of speed and intelligence.

**Download Steps:**

1. Click the **🔍 Search/Download** icon (left sidebar)
2. In the search bar, type: `qwen2.5-7b-instruct`
3. Look for: **Qwen/Qwen2.5-7B-Instruct-GGUF**
4. Click the **↓ Download** button next to: `qwen2.5-7b-instruct-q4_k_m.gguf`
5. Wait for download to complete (4.7GB)

### Alternative Models

If you have limited RAM or want faster processing:

| Model                          | Size  | RAM Needed | Quality   |
| ------------------------------ | ----- | ---------- | --------- |
| **qwen2.5-7b-instruct-q4_k_m** | 4.7GB | 8GB        | ✅ Best   |
| llama-3.2-3b-instruct-q4_k_m   | 2GB   | 4GB        | Good      |
| phi-3-mini-4k-instruct-q4      | 2.3GB | 6GB        | Good      |
| mistral-7b-instruct-v0.2-q4    | 4.1GB | 8GB        | Excellent |

---

## Step 4: Load the Model

1. Click the **Local Server** tab (left sidebar, looks like `<>`)
2. At the top, click the **Select a model** dropdown
3. Choose your downloaded model (e.g., `qwen2.5-7b-instruct`)
4. Wait 30-60 seconds for model to load
5. You'll see "Model loaded" in the status area

---

## Step 5: Configure Server Settings

Before starting, configure these settings (click gear icon):

### Recommended Settings

```
Context Length: 4096
GPU Offload: Auto (or all layers if you have a GPU)
```

### For Low RAM Systems (8GB)

```
Context Length: 2048
GPU Offload: None
```

---

## Step 6: Start the Server

1. Click the **Start Server** button (green play button)
2. Wait until you see: `Running on http://localhost:1234`
3. The status indicator should turn **green**

---

## Step 7: Verify the Server

Open a terminal and run:

```bash
curl http://localhost:1234/v1/models
```

**Expected Response:**

```json
{
  "data": [
    {
      "id": "qwen2.5-7b-instruct",
      "object": "model",
      "created": 1234567890,
      "owned_by": "lmstudio"
    }
  ]
}
```

---

## Step 8: Configure the Project

Make sure your `.env` file has these settings:

```bash
# LM Studio Settings
USE_LOCAL_LLM=true
LLM_MODEL=qwen2.5-7b-instruct
LLM_ENDPOINT=http://localhost:1234/v1/chat/completions
LLM_TEMPERATURE=0.2
LLM_TIMEOUT=120
LLM_MAX_TOKENS=2000
```

---

## Step 9: Test the Integration

Run a quick test:

```bash
uv run python tests/test_lmstudio_direct.py
```

**Expected Output:**

```
✅ LM Studio connection successful
Model: qwen2.5-7b-instruct
Response: [AI response here]
```

---

## Running Without LM Studio (Fallback Mode)

If LM Studio is not available, the system can run in basic mode:

```bash
# Disable AI
USE_LOCAL_LLM=false uv run python -m src.cli_v2 "housing prices"
```

In fallback mode:

- ✅ Data download works
- ✅ Basic cleaning (remove empty columns)
- ❌ No AI-powered query expansion
- ❌ No intelligent cleaning decisions

---

## Troubleshooting

### "Connection refused" error

**Cause:** LM Studio server not running

**Solution:**

1. Open LM Studio
2. Go to Local Server tab
3. Click Start Server
4. Verify green status indicator

### "Model not found" error

**Cause:** Wrong model name in `.env`

**Solution:**

1. In LM Studio, check exact model name (lowercase)
2. Update `LLM_MODEL` in `.env` to match

### Slow response times

**Cause:** Model too large for RAM

**Solution:**

1. Use a smaller model (Phi-3 Mini)
2. Reduce context length to 2048
3. Close other applications

### Out of memory crash

**Cause:** Model + data exceeds RAM

**Solution:**

1. Close LM Studio
2. Process data with `USE_LOCAL_LLM=false`
3. Restart LM Studio after processing

---

## Tips for Best Performance

1. **Keep LM Studio running in background** while processing datasets
2. **Use GPU offloading** if you have a dedicated graphics card
3. **Close other heavy apps** (browsers, games) during processing
4. **Use SSD storage** for faster model loading

---

## Quick Reference

### Start LM Studio Server

1. Open LM Studio
2. Local Server tab → Start Server OR(lms server start ) for stopping server (lms server stop)
3. Wait for green "Running" status

### Verify Server

```bash
curl http://localhost:1234/v1/models
```

### Stop Server

1. LM Studio → Stop Server button
2. Or close LM Studio completely

---

**LM Studio is now configured! 🎉**
