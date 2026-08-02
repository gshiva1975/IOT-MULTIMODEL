# networksecurity -- containerized deployment.
#
# Build:
#   docker build -t networksecurity .
#
# Run (mount your data + results dirs from the host; pass the API key at runtime,
# never bake it into the image):
#   docker run --rm \
#     -e ANTHROPIC_API_KEY=sk-ant-... \
#     -v "$(pwd)/data:/app/data" \
#     -v "$(pwd)/results:/app/results" \
#     networksecurity \
#     python3 scripts/run_pipeline.py --data-dir data/CSV --limit 5 --samples-per-class 5
#
# Free report generation (no API key needed if results/ already has data):
#   docker run --rm \
#     -v "$(pwd)/results:/app/results" \
#     networksecurity \
#     python3 scripts/generate_rag_report.py

FROM python:3.11-slim

WORKDIR /app

# matplotlib needs a small amount of system font/rendering support even in Agg mode
RUN apt-get update && apt-get install -y --no-install-recommends \
    libfreetype6 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY scripts/ scripts/

RUN mkdir -p data results

ENV PYTHONUNBUFFERED=1

ENTRYPOINT []
CMD ["python3", "scripts/run_pipeline.py", "--help"]
