web: gunicorn scripts.runserver:app
worker: celery worker --app=app.celery -Q sending -P solo --loglevel=info