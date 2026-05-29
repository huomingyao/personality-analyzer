"""Configuration management for Psyche KB."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)


def get_minimax_api_key() -> str:
    """Get MiniMax API key from environment variable."""
    api_key = os.getenv("MINIMAX_API")
    if not api_key:
        msg = "MINIMAX_API environment variable not set"
        raise EnvironmentError(msg)
    return api_key


def get_minimax_model() -> str:
    """Get MiniMax model name."""
    return os.getenv("MINIMAX_MODEL", "MiniMax-M2.7")


# Vector store config
VECTOR_DIM = 1024  # Embedding dimension for MiniMax-M2.7
FAISS_INDEX_PATH = DATA_DIR / "faiss_index.bin"