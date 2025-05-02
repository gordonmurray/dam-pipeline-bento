FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .

# Force-remove any pre-installed torch (cached layers or base image leftovers)
RUN pip uninstall -y torch || true

# Install CPU-only PyTorch
RUN pip install --no-cache-dir torch==2.2.2+cpu \
    --extra-index-url https://download.pytorch.org/whl/cpu

# Install everything else
RUN pip install --no-cache-dir -r requirements.txt

COPY worker.py .

CMD ["python", "worker.py"]
