from flask import Flask
from flask_restful import Api
from flask_cors import CORS
from flasgger import Swagger
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from celery import Celery
from celery.app.task import Task
from .config import Config

__all__ = ['app', 'db', 'api', 'mail', 'celery', 'Config']


app = Flask(__name__)
app.config.from_object(Config)
CORS(app)
Swagger(app)

celery = Celery(app.import_name,
                broker=app.config['CELERY_BROKER_URL'],
                include=['api.mixins'],
                task_cls=Task)
celery.conf.update(app.config)

db = SQLAlchemy(app)

mail = Mail(app)

api = Api(app)
