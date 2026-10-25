FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ src/
COPY solution/ solution/
# demo bundle (dashboard + live workbench): python -m solution demo --host 0.0.0.0
COPY demo/ demo/
COPY examples/ examples/
COPY data/public_test.csv data/public_test.csv
ENV PYTHONUNBUFFERED=1 LLM_CACHE_DIR=/tmp/llm-cache
ENTRYPOINT ["python", "-m", "solution"]
# docker run ... IMAGE adapt  -> reads /input/train.jsonl, writes /artifacts
# docker run ... IMAGE eval   -> reads /input/test.jsonl + /artifacts, writes /output/predictions.csv
