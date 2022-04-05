web: gunicorn scripts.runserver:app
worker: celery -A app.celery worker -Q sending -P solo --loglevel=info