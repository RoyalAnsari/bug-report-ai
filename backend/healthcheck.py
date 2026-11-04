import os
import sys
import urllib.request

port = os.getenv("PORT", "8000")
try:
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/v1/health", timeout=5) as response:
        sys.exit(0 if response.status < 500 else 1)
except Exception:
    sys.exit(1)
