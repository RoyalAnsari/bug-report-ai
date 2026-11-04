"""Container ka shuruaati script: pehle models ki jaanch (zaroorat par download), phir server."""
import os
import sys

import fetch_models


def main():
    code = fetch_models.main()
    if code:
        sys.exit(code)
    port = os.getenv("PORT", "8000")
    os.execv(
        sys.executable,
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", port],
    )


if __name__ == "__main__":
    main()
