FROM python:3.10-slim
WORKDIR /app
ENV PYTHONPATH=/app
COPY . .
CMD ["python","server/server.py"]
