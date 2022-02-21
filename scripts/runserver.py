from app import app, api, Config
from api.views import *

if __name__ == '__main__':
    api.add_resource(EchoView, "/")
    api.add_resource(AccountsViewSet, "/account/")
    app.run(debug=Config.DEBUG_MODE)
