import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration (Groq)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in environment variables")

# Directory paths
DOCUMENTS_DIR = os.getenv("DOCUMENTS_DIR", "./documents")
OKF_BUNDLE_DIR = os.getenv("OKF_BUNDLE_DIR", "./okf_bundle")
