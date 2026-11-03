import sys
from pathlib import Path

# backend folder ko path mein dalta hai, taake "from app.ml..." chal sake
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))