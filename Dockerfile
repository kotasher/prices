FROM python:3.11-alpine
WORKDIR /app
RUN pip install --no-cache-dir --upgrade fastapi httpx redis unicorn gunicorn
COPY ./*.py /app/
CMD ["gunicorn", "--workers", "3", "-k", "uvicorn.workers.UvicornWorker", "main:app", "-b", "0.0.0.0:8000"]