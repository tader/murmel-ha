FROM python:3.13-slim-bookworm
LABEL org.opencontainers.image.source="https://github.com/tader/murmel-ha"
LABEL org.opencontainers.image.licenses="MIT"
ENV PYTHONUNBUFFERED=1 HF_HUB_DISABLE_TELEMETRY=1 HF_HUB_DISABLE_PROGRESS_BARS=1
RUN apt-get update && apt-get install -y --no-install-recommends libsndfile1 libgomp1 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt
COPY wyoming_murmel ./wyoming_murmel
EXPOSE 10300
CMD ["python", "-m", "wyoming_murmel"]
