# Build context repo ka root hota hai (docker build -f backend/Dockerfile .), kyunke backend ko ml/src bhi chahiye.
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Folder ka naqsha repo jaisa hi rakhte hain: backend/app/ml/inference.py REPO_ROOT ko parents[3] se nikalta hai.
WORKDIR /app/backend

# Pehle CPU wala torch (CUDA wala bohat bara hota hai), phir baqi packages.
RUN pip install --index-url https://download.pytorch.org/whl/cpu torch
COPY backend/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

COPY backend/ ./
COPY ml/src /app/ml/src

# Models image mein nahi hote: woh /app/ml/artifacts mein mount hote hain ya start par download hote hain.
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/ml/artifacts \
    && chown -R appuser:appuser /app
USER appuser

ENV PORT=8000
EXPOSE 8000

# Models load hone mein kuch der lagti hai, is liye start-period lamba hai.
HEALTHCHECK --interval=30s --timeout=10s --start-period=180s --retries=3 CMD ["python", "healthcheck.py"]

CMD ["python", "start.py"]
