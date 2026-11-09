FROM python:3.11-slim

WORKDIR /app

# Set pip to use a longer timeout and more retries for slow connections
ENV PIP_DEFAULT_TIMEOUT=300
ENV PIP_RETRIES=5
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

COPY . .
RUN chmod +x entrypoint.sh

# Pre-download required NLTK tokenizers
RUN python -c "import nltk; nltk.download('stopwords', quiet=True); nltk.download('punkt', quiet=True)"

EXPOSE 5000

CMD ["/bin/bash", "/app/entrypoint.sh"]
