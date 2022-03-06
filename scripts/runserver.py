from app import app, api, Config
from api.views import *

if __name__ == '__main__':
    api.add_resource(FileView, "/upload/<path:path>")
    api.add_resource(AccountView, "/account/")
    api.add_resource(TokenView, "/account/token/")
    api.add_resource(CaseCreateView, "/case/add/")
    app.run(debug=Config.DEBUG_MODE)
