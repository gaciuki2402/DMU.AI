import os
from dotenv import load_dotenv

def load_environment():
    load_dotenv()
    
    critical_vars = ['OPENAI_API_KEY', 'DATABASE_URL', 'API_URL']
    missing_vars = []

    for var in critical_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        elif var == 'OPENAI_API_KEY':
            # Explicitly set OPENAI_API_KEY in environment
            os.environ["OPENAI_API_KEY"] = value

    if missing_vars:
        raise ValueError(f"Missing critical environment variables: {', '.join(missing_vars)}. Please set these in your .env file or environment.")

    # Optional: Log successful loading of environment variables
    print("Environment variables loaded successfully.")