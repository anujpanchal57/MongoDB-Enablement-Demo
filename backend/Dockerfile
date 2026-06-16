# FastAPI backend image for AWS Lambda (container image) — and any container host.
# Python 3.13 — matches the project's supported runtime.
#
# Runs uvicorn unchanged on Lambda via the AWS Lambda Web Adapter (LWA), so the
# FastAPI lifespan (async Mongo connect/disconnect) and all async code work as-is
# — no Mangum handler or code changes needed. LWA is a no-op when run locally.
FROM public.ecr.aws/docker/library/python:3.13-slim

# AWS Lambda Web Adapter extension. Bump the tag to the latest release as needed.
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.8.4 /lambda-adapter /opt/extensions/lambda-adapter

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Port uvicorn listens on AND the port LWA forwards Lambda events to.
    PORT=8000 \
    AWS_LWA_PORT=8000 \
    # Wait for the app (and its Mongo connection) to be ready before serving.
    AWS_LWA_READINESS_CHECK_PATH=/health

WORKDIR /app

# Install dependencies first for better layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code.
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
