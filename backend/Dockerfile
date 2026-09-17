FROM python:3.10-slim

WORKDIR /app

# Set pip to use a longer timeout and more retries for slow connections
ENV PIP_DEFAULT_TIMEOUT=300
ENV PIP_RETRIES=5

COPY requirements.txt .
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

COPY . .

# NLTK data needed at runtime by preprocess.py
RUN python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt')"

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
