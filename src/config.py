from pathlib import Path
import os


ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
LOG_DIR = ROOT_DIR / "logs"

SQLITE_PATH = DATA_DIR / "local.db"
VECTOR_PATH = DATA_DIR / "vectors.json"
KEYWORD_INDEX_PATH = DATA_DIR / "keyword_index.json"

DOUBAO_API_KEY = os.getenv("DOUBAO_API_KEY", "")
DOUBAO_BASE_URL = os.getenv("DOUBAO_BASE_URL", "")
DOUBAO_MODEL = os.getenv("DOUBAO_MODEL", "doubao-pro")

MAX_AGENT_STEPS = int(os.getenv("MAX_AGENT_STEPS", "6"))
