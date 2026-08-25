FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY catalog.json ./catalog.json

# Сервис ничего не пишет на диск: заказы живут в postgres, поэтому
# контейнер можно удалить и поднять заново в любой момент.
RUN useradd --system --uid 10001 shop && chown -R shop /app
USER shop

EXPOSE 8080
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers", "--forwarded-allow-ips", "*"]
