from app import app, api, Config
from api.views import *

api.add_resource(FileView, "/upload/<path:path>")
api.add_resource(AccountView, "/account/")
api.add_resource(TokenView, "/account/token/")
api.add_resource(CaseCreateView, "/case/add/")
api.add_resource(CaseEditorView, "/case/<id>/")
api.add_resource(CaseDocumentAdder, "/case/<case_id>/<category>/")
api.add_resource(CaseViewSet, "/cases/")
api.add_resource(AdminCaseSubmitView, "/staff/case/<id>/<step>/")
