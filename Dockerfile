FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

CMD python manage.py migrate --noinput && (python manage.py createsuperuser --noinput || true) && exec gunicorn --bind :$PORT --workers 2 core.wsgi:application
