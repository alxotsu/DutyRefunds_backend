from app import app, api, Config
from api.views import *


api.add_resource(FileView, "/upload/<path:path>")
api.add_resource(AccountsViewSet, "/account/")
api.add_resource(AccountView, "/account/<int:id>/")
api.add_resource(TokenView, "/account/token/")
