FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HOST=0.0.0.0 PORT=8765 AUTOWORTH_DB=/data/autoworth.sqlite3
WORKDIR /app
COPY autoworth_server.py car_valuation.html ./
EXPOSE 8765
CMD ["python", "autoworth_server.py"]
