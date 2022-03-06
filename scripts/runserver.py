from app import app, api, Config
from api.views import *

api.add_resource(FileView, "/upload/<path:path>")
api.add_resource(AccountView, "/account/")
api.add_resource(TokenView, "/account/token/")
api.add_resource(CaseCreateView, "/case/add/")
api.add_resource(CaseEditorView, "/case/<id>/")
