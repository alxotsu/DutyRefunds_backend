from flask import Flask
from flask_restful import Api
from flask_cors import CORS
from flasgger import Swagger
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail

from .config import Config

__all__ = ['app', 'db', 'api', 'mail' 'Config']


app = Flask(__name__)
app.config.from_object(Config)
CORS(app)
Swagger(app)

db = SQLAlchemy(app)

mail = Mail(app)

api = Api(app)
