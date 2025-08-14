from fastapi import FastAPI, Form, HTTPException
import requests
import logging
import re
from fastapi.middleware.cors import CORSMiddleware

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use a smaller model that requires less memory
MODEL_NAME = "phi"  # Phi is a smaller model that should work on systems with limited memory

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    """Simple health check endpoint"""
    return {"status": "ok", "model": MODEL_NAME}

@app.post("/analyze/")
def analyze_sentiment(text: str = Form(...)):
    if not text.strip():
        return {"sentiment": "Please provide some text to analyze"}
    
    # Try using a different model that's smaller and might be available
    global MODEL_NAME
    
    # First check if Ollama is running at all
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
    
    # Modified prompt to get a more reliable response format
    prompt = f"""Analyze the sentiment of the following text and respond with EXACTLY ONE WORD (Positive, Negative, or Neutral).
Text: {text}
Sentiment:"""
    
    try:
        # Try to connect to Ollama API
        logger.info(f"Attempting to use model: {MODEL_NAME}")
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": MODEL_NAME, "prompt": prompt, "stream": False},
            timeout=15  # Longer timeout
        )
        
        # Check if request was successful
        response.raise_for_status()
        
        # Parse the JSON response
        result = response.json()
        
        # Extract sentiment from response
        if "response" in result:
            raw_sentiment = result["response"].strip()
            sentiment_match = re.search(r'(Positive|Negative|Neutral)', raw_sentiment, re.IGNORECASE)
            
            if sentiment_match:
                sentiment = sentiment_match.group(0)
                sentiment = sentiment.capitalize()
                return {"sentiment": sentiment}
            else:
                return {"sentiment": raw_sentiment[:50]} 
        else:
            logger.error(f"Missing 'response' key in API result: {result}")
            return {"sentiment": "Error: Unable to analyze sentiment"}
            
    except requests.exceptions.ConnectionError:
        logger.error("Failed to connect to Ollama API")
        return {"sentiment": "Error: Cannot connect to Ollama. Run 'ollama serve' in a terminal"}
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        if "model not found" in str(e).lower():
            # Try to pull the model automatically
            try:
                import subprocess
                logger.info(f"Trying to pull model {MODEL_NAME}")
                subprocess.Popen(["ollama", "pull", MODEL_NAME])
                return {"sentiment": f"Model {MODEL_NAME} not found. Attempting to download it now. Please try again in a minute."}
            except:
                return {"sentiment": f"Error: Model not found. Run 'ollama pull {MODEL_NAME}' in a terminal"}
        return {"sentiment": f"Error connecting to Ollama API"}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"sentiment": "Unexpected error occurred"}