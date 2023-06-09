from app import app, api, Config
from api.views import *

__all__ = ['main']

api.add_resource(FileView, "/upload/<path:path>")
api.add_resource(AccountView, "/account/")
api.add_resource(TokenView, "/account/token/")
api.add_resource(CaseCreateView, "/case/add/")
api.add_resource(CaseEditorView, "/case/<int:id>/")
api.add_resource(CaseDocumentAdder, "/case/<int:case_id>/<category>/")
api.add_resource(CaseViewSet, "/cases/")
api.add_resource(AdminCaseSubmitView, "/staff/case/<int:id>/<step>/")


def main():
    app.run(debug=Config.DEBUG_MODE)


if __name__ == '__main__':
    main()
