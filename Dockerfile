FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ src/
COPY solution/ solution/
ENV PYTHONUNBUFFERED=1 LLM_CACHE_DIR=/tmp/llm-cache
ENTRYPOINT ["python", "-m", "solution"]
# docker run ... IMAGE adapt  -> reads /input/train.jsonl, writes /artifacts
# docker run ... IMAGE eval   -> reads /input/test.jsonl + /artifacts, writes /output/predictions.csv
