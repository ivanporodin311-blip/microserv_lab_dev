# ЭТАП 1: Сборщик (Builder)
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
# Устанавливаем пакеты в специальную папку, а не в директорию root
RUN pip install --no-cache-dir --target=/app/deps -r requirements.txt

# ЭТАП 2: Рабочий образ (Runtime)
FROM python:3.11-slim

WORKDIR /app

# Копируем установленные зависимости из этапа builder
COPY --from=builder /app/deps /app/deps
# Добавляем эту папку в путь поиска модулей Python
ENV PYTHONPATH=/app/deps

# Копируем исходный код приложения
COPY main.py .

# Создаем непривилегированного пользователя для безопасности 
# и выдаем ему полные права на всю папку /app
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Запускаем приложение через python -m, чтобы гарантированно найти uvicorn в PYTHONPATH
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]