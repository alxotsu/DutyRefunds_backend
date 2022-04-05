web: gunicorn scripts.runserver:app
worker: celery --app=app.celery worker -Q sending -P solo --loglevel=info