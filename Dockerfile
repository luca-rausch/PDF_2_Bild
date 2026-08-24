# Schlankes Python-Image, keine System-Abhaengigkeiten noetig dank PyMuPDF (statisch gelinktes MuPDF)
FROM python:3.11-slim

WORKDIR /app

# Requirements zuerst kopieren fuer besseres Docker-Layer-Caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Nicht-root User aus Sicherheitsgruenden
RUN useradd -m appuser
USER appuser

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]
