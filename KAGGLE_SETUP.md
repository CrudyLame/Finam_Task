# Using Lightweight LLMs on Kaggle

This guide shows how to use various lightweight LLM providers instead of OpenAI for conversation analysis on Kaggle.

## 🚀 Quick Start Options

### Option 1: Hugging Face (FREE, Local)
**Best for**: Kaggle notebooks, no API costs
**Requirements**: GPU-enabled Kaggle notebook

```python
# Install requirements
!pip install transformers torch accelerate

# Configuration
llm_config = {
    'llm_provider': 'huggingface',
    'model_name': 'microsoft/Phi-3-mini-4k-instruct'
}
```

**Recommended Models**:
- `microsoft/Phi-3-mini-4k-instruct` - 3.8B params, best balance
- `google/gemma-2b-it` - 2B params, faster
- `microsoft/DialoGPT-medium` - 345M params, fastest

### Option 2: Groq (FAST, API-based)
**Best for**: Fastest inference, free tier available
**Requirements**: Free Groq API key

```python
# Install requirements
!pip install groq

# Configuration
llm_config = {
    'llm_provider': 'groq',
    'api_key': 'your_groq_api_key_here',
    'model_name': 'llama3-8b-8192'
}
```

**Get API Key**: https://console.groq.com/

### Option 3: Ollama (LOCAL)
**Best for**: Local development
**Requirements**: Ollama running locally

```python
# Install requirements
!pip install ollama

# Configuration
llm_config = {
    'llm_provider': 'ollama',
    'model_name': 'llama3.1:8b',
    'base_url': 'http://localhost:11434'
}
```

## 📊 Performance Comparison

| Provider | Speed | Cost | Quality | Memory | Setup |
|----------|-------|------|---------|---------|--------|
| OpenAI | Medium | $$$ | Excellent | Low | Easy |
| Hugging Face | Fast | FREE | Good | High | Medium |
| Groq | Very Fast | $ | Good | Low | Easy |
| Ollama | Medium | FREE | Good | Medium | Hard |

## 🔧 Kaggle Setup Instructions

### For Hugging Face:

1. **Enable GPU**: Settings → Accelerator → GPU T4 x2
2. **Install dependencies**:
   ```bash
   !pip install transformers torch accelerate bitsandbytes
   ```
3. **Use the configuration** in the notebook cell

### For Groq:

1. **Get API key**: Visit https://console.groq.com/
2. **Install dependency**:
   ```bash
   !pip install groq
   ```
3. **Add API key** to Kaggle Secrets or directly in config

### Memory Requirements:

- **Phi-3-mini (3.8B)**: ~8GB VRAM
- **Gemma-2B**: ~4GB VRAM  
- **DialoGPT-medium**: ~2GB VRAM

## 🛠️ Configuration Examples

### Minimal Memory (2GB):
```python
llm_config = {
    'llm_provider': 'huggingface',
    'model_name': 'microsoft/DialoGPT-medium'
}
```

### Balanced (8GB):
```python
llm_config = {
    'llm_provider': 'huggingface',
    'model_name': 'microsoft/Phi-3-mini-4k-instruct'
}
```

### Fastest Inference:
```python
llm_config = {
    'llm_provider': 'groq',
    'api_key': 'your_key_here',
    'model_name': 'llama3-8b-8192'
}
```

## 🔍 Troubleshooting

### Common Issues:

1. **Out of Memory**: Use smaller model or reduce batch size
2. **Slow inference**: Enable GPU acceleration
3. **API limits**: Use free tier limits or switch to local models

### Performance Tips:

- Use GPU-enabled Kaggle notebooks
- Reduce `max_concurrent_requests` for stability
- Use smaller `batch_size` for memory efficiency
- Enable model quantization for Hugging Face models

## 💡 Model Selection Guide

### For Russian Text (like your data):
- **Phi-3-mini**: Good multilingual support
- **Gemma-2B**: Decent Russian support
- **Llama-3**: Excellent Russian support (via Groq)

### For Speed Priority:
1. Groq (fastest API)
2. DialoGPT-medium (fastest local)
3. Gemma-2B (fast local)

### For Quality Priority:
1. Llama-3 (via Groq)
2. Phi-3-mini (local)
3. Gemma-2B (local)

## 🎯 Recommended Setup for Kaggle

```python
# Best balance of speed, cost, and quality
llm_config = {
    'llm_provider': 'huggingface',
    'model_name': 'microsoft/Phi-3-mini-4k-instruct'
}

processing_config = {
    'max_concurrent_requests': 3,  # Conservative for stability
    'batch_size': 20,  # Smaller batches
}
```

This setup should work well on Kaggle's free GPU tier and provide good analysis quality for your Russian conversation data.