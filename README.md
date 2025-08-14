# Sentiment Analyzer with TinyLlama

This project is a simple sentiment analysis web application that uses a FastAPI backend and a Streamlit frontend. The backend leverages language models via the Ollama API to analyze the sentiment of user-provided text.

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Backend Details](#backend-details)
- [Frontend Details](#frontend-details)
- [Setup & Installation](#setup--installation)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Troubleshooting Guide](#troubleshooting-guide)
- [License](#license)

## Overview

This application allows users to input text and receive a sentiment analysis (Positive, Negative, or Neutral) using lightweight language models via Ollama. The backend is built with FastAPI and communicates with the Ollama API to generate sentiment predictions.

## Tech Stack

- **Backend:** FastAPI (Python)
- **Frontend:** Streamlit (Python)
- **Model:** TinyLlama via Ollama API
- **HTTP Client:** `requests` library
- **Dependencies:** Python 3.11+, FastAPI, Streamlit, Ollama

## Project Structure

```
sentiment-analyzer-mistral/
├── README.md
├── backend/
│   └── main.py
├── frontend/
│   └── app.py
└── venv/
```

## Backend Details

The backend is implemented in FastAPI and exposes a POST endpoint `/analyze/` that accepts text input and returns the sentiment analysis.

### Key Code Snippet

```python
@app.post("/analyze/")
def analyze_sentiment(text: str = Form(...)):
    # Formulate the prompt for the model
    prompt = f"""Analyze the sentiment of the following text and respond with EXACTLY ONE WORD (Positive, Negative, or Neutral).
Text: {text}
Sentiment:"""
    
    # Send to Ollama API
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": MODEL_NAME, "prompt": prompt, "stream": False}
    )
    
    # Extract sentiment from response
    result = response.json()
    if "response" in result:
        raw_sentiment = result["response"].strip()
        sentiment_match = re.search(r'(Positive|Negative|Neutral)', raw_sentiment, re.IGNORECASE)
        
        if sentiment_match:
            sentiment = sentiment_match.group(0).capitalize()
            return {"sentiment": sentiment}
    
    return {"sentiment": "Error: Unable to analyze sentiment"}
```

## Frontend Details

The frontend is built with Streamlit and provides a simple user interface to enter text and view sentiment analysis results.

### Key Features

- Text input area
- Pre-defined examples (positive, negative, neutral)
- Sentiment display with appropriate emoji and color
- System status indicators for backend and Ollama
- Troubleshooting assistance

### Key Code Snippet

```python
if st.button("Analyze Sentiment"):
    if not text_input.strip():
        st.error("Please enter some text to analyze")
    else:
        with st.spinner("Analyzing sentiment..."):
            try:
                res = requests.post("http://localhost:8000/analyze/", 
                                  data={"text": text_input},
                                  timeout=30)
                
                if res.status_code == 200:
                    sentiment = res.json().get("sentiment", "Error")
                    
                    # Display appropriate emoji and color
                    if sentiment == "Positive":
                        st.success(f"Sentiment: {sentiment} 😀")
                    elif sentiment == "Negative":
                        st.error(f"Sentiment: {sentiment} 😞")
                    elif sentiment == "Neutral":
                        st.info(f"Sentiment: {sentiment} 😐")
```

## Setup & Installation

### Prerequisites

- Python 3.11+
- Ollama installed on your system ([installation guide](https://github.com/ollama/ollama#installation))
- Minimum 2GB RAM (for TinyLlama)

### Install Dependencies

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install fastapi uvicorn streamlit requests python-multipart
```

### Start Ollama and Pull Model

```bash
# Start Ollama (if not already running)
ollama serve

# Pull TinyLlama model (requires ~637MB)
ollama pull tinyllama
```

### Run the Application

```bash
# Terminal 1: Start backend
cd backend
uvicorn main:app --reload

# Terminal 2: Start frontend
cd frontend
streamlit run app.py
```

## Usage

1. Open the Streamlit frontend in your browser (typically at http://localhost:8501)
2. Enter text or select an example
3. Click "Analyze Sentiment"
4. View the sentiment result with emoji indicator

## API Reference

### POST `/analyze/`

- **Description:** Analyze the sentiment of the provided text.
- **Request Body:** Form data with a single field `text`.
- **Response:** JSON object with the sentiment.

## Troubleshooting Guide

### Memory Issues

**Problem:** Error message about insufficient memory

```
Error: 500 Internal Server Error: model requires more system memory (4.9 GiB) than is available (1.9 GiB)
```

**Solution:** Use a smaller model that requires less memory

```bash
# Pull TinyLlama instead of Mistral
ollama pull tinyllama

# Or try even smaller models
ollama pull phi
ollama pull gemma:2b
```

Then update the `MODEL_NAME` variable in both frontend and backend:

```python
# In backend/main.py and frontend/app.py
MODEL_NAME = "tinyllama"  # or "phi" or "gemma:2b"
```

### Backend Connection Issues

**Problem:** Frontend shows "Backend server is offline"

**Solution:**

1. Make sure backend is running:
```bash
cd backend
uvicorn main:app --reload
```

2. Check for port conflicts - if port 8000 is used, specify another:
```bash
uvicorn main:app --reload --port 8001
```
Then update the frontend's URL to match.

### Ollama Connection Issues

**Problem:** "Error connecting to Ollama API"

**Solution:**

1. Check if Ollama is running:
```bash
curl http://localhost:11434/api/tags
```

2. If not running, start it:
```bash
ollama serve
```

3. If you get "address already in use" error, Ollama is already running:
```
Error: listen tcp 127.0.0.1:11434: bind: address already in use
```

4. Update the backend code to auto-select an available model:

```python
try:
    check_response = requests.get("http://localhost:11434/api/tags", timeout=3)
    # Ollama is running, check available models
    if check_response.status_code == 200:
        models = check_response.json().get("models", [])
        available_models = [m["name"] for m in models]
        logger.info(f"Available models: {available_models}")
        
        # Try smaller models in order
        for model_option in ["phi", "tinyllama", "gemma:2b", "llama2"]:
            if model_option in available_models:
                MODEL_NAME = model_option
                logger.info(f"Selected model: {MODEL_NAME}")
                break
except Exception as e:
    logger.error(f"Could not check Ollama: {e}")
    return {"sentiment": "Error: Ollama is not running. Start with 'ollama serve'"}
```

### Missing Models

**Problem:** Error message about model not found

**Solution:** Pull the required model:

```bash
# List available models
ollama list

# Pull needed model
ollama pull tinyllama
```

### Complete Error Handling

For comprehensive error handling in your backend, update your code to:

```python
@app.post("/analyze/")
def analyze_sentiment(text: str = Form(...)):
    if not text.strip():
        return {"sentiment": "Please provide some text to analyze"}
    
    try:
        # Try to connect to Ollama API
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": MODEL_NAME, "prompt": prompt, "stream": False},
            timeout=15
        )
        
        # Check if request was successful
        response.raise_for_status()
        
        # Process response
        # ...
            
    except requests.exceptions.ConnectionError:
        logger.error("Failed to connect to Ollama API")
        return {"sentiment": "Error: Cannot connect to Ollama. Run 'ollama serve' in a terminal"}
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        return {"sentiment": f"Error connecting to Ollama API"}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"sentiment": "Unexpected error occurred"}
```

## License

This project is licensed under the MIT License.

