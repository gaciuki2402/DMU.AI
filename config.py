import os
from dotenv import load_dotenv

def load_environment():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("No OpenAI API key found. Please set the OPENAI_API_KEY environment variable.")
    os.environ["OPENAI_API_KEY"] = api_key
    