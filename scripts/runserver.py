from app import app, api, Config
from api.views import *

if __name__ == '__main__':
    api.add_resource(FileView, "/upload/<path:path>")
    api.add_resource(AccountsViewSet, "/account/")
    api.add_resource(AccountView, "/account/<int:id>/")
    api.add_resource(TokenView, "/account/<int:id>/confirm/")
    app.run(debug=Config.DEBUG_MODE)
