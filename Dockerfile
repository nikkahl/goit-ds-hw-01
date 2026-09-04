FROM python:3.12-slim

WORKDIR /app

# Спочатку копіюємо тільки конфіги Poetry — для кешування шару залежностей
COPY pyproject.toml poetry.lock* ./

RUN pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

COPY . .

ENTRYPOINT ["python", "hw8/main.py"]