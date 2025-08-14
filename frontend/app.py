import streamlit as st
import requests

# Model name should match what's used in the backend
MODEL_NAME = "tinyllama"  # Using tinyllama since you just pulled it

st.set_page_config(page_title="Sentiment Analyzer", page_icon="😀")

st.title(f"Sentiment Analyzer ({MODEL_NAME.capitalize()})")

# Check backend status
backend_status = st.empty()
try:
    # Simple ping to see if backend is running
    response = requests.get("http://localhost:8000/")
    if response.status_code == 200:
        backend_status.success("✅ Backend server is online")
    else:
        backend_status.warning("⚠️ Backend server responded with status code: " + str(response.status_code))
except Exception as e:
    backend_status.error("❌ Backend server is offline. Run 'uvicorn main:app --reload' in the backend folder")

st.write(f"This app analyzes the sentiment of text using the {MODEL_NAME.capitalize()} AI model.")

# Add some example text options
examples = [
    "I love this product! It's amazing and exceeded all my expectations.",
    "This is the worst experience I've ever had. Terrible customer service.",
    "The weather today is neither good nor bad, just average."
]

example_choice = st.selectbox("Try an example:", ["", "Positive example", "Negative example", "Neutral example"])

if example_choice:
    if example_choice == "Positive example":
        text_input = examples[0]
    elif example_choice == "Negative example":
        text_input = examples[1]
    else:
        text_input = examples[2]
else:
    text_input = st.text_area("Enter your text here:", height=150)

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
                    
                    # Display appropriate emoji and color based on sentiment
                    if sentiment == "Positive":
                        st.success(f"Sentiment: {sentiment} 😀")
                    elif sentiment == "Negative":
                        st.error(f"Sentiment: {sentiment} 😞")
                    elif sentiment == "Neutral":
                        st.info(f"Sentiment: {sentiment} 😐")
                    elif "Error" in sentiment:
                        st.error(sentiment)
                    else:
                        st.warning(f"Sentiment: {sentiment}")
                else:
                    st.error(f"Error: Received status code {res.status_code}")
                    
            except requests.exceptions.ConnectionError:
                st.error("Failed to connect to the backend server. Is it running?")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

st.divider()

# Show system status section
st.subheader("System Status")
col1, col2 = st.columns(2)

with col1:
    st.write("**Backend Server**")
    if st.button("Check Backend"):
        try:
            resp = requests.get("http://localhost:8000/")
            st.success("✅ Backend is running")
        except:
            st.error("❌ Backend is not running")

with col2:
    st.write("**Ollama API**")
    if st.button("Check Ollama"):
        try:
            resp = requests.get("http://localhost:11434/api/tags")
            st.success("✅ Ollama is running")
            
            # Check if our model is available
            try:
                models = resp.json().get("models", [])
                if any(m["name"] == MODEL_NAME for m in models):
                    st.success(f"✅ {MODEL_NAME} model is available")
                else:
                    st.warning(f"⚠️ {MODEL_NAME} model not found. Run 'ollama pull {MODEL_NAME}'")
            except:
                st.warning("⚠️ Could not check for model availability")
        except:
            st.error("❌ Ollama is not running")

# Setup instructions
st.subheader("Setup Instructions")
st.write(f"1. Make sure Ollama is running with the {MODEL_NAME} model installed.")
st.write("2. Start the backend server with: `uvicorn main:app --reload`")
st.write("3. Start the frontend with: `streamlit run app.py`")
st.caption(f"To install the model: `ollama pull {MODEL_NAME}`")
st.caption(f"Note: The Mistral model requires 4.9 GiB of memory, which is more than the available 1.9 GiB on this system.")
st.caption("Using tinyllama as a lighter alternative that requires less memory.")