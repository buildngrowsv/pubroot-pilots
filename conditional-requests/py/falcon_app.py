# Falcon 4 ASGI app with add_static_route (falcon.routing.StaticRoute) served by uvicorn; run: uvicorn py.falcon_app:app
import os
import falcon.asgi
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
app = falcon.asgi.App(); app.add_static_route("/", os.path.abspath(DATA))
