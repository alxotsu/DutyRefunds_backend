from app import app, api, Config
from api.views import EchoView

if __name__ == '__main__':
    api.add_resource(EchoView, "/")
    app.run(debug=Config.DEBUG_MODE)
