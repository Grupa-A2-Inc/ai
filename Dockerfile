FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser \
    && chown appuser:appgroup /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt \
    && chmod a-w requirements.txt

COPY manage.py .
COPY adaptive_ai ./adaptive_ai
COPY tutoring ./tutoring

RUN chmod -R a-w manage.py adaptive_ai tutoring

EXPOSE 8000

USER appuser

CMD ["sh", "-c", "python manage.py migrate && gunicorn adaptive_ai.wsgi:application --bind 0.0.0.0:8000"]
