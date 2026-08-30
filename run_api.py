import sys
sys.path.insert(0, ".")  # add project root to path
from src.api.main import app  # noqa: F401 (needed for uvicorn to find it)