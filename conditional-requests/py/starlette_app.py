# Starlette StaticFiles (its static-file app; FileResponse alone evaluates no preconditions) served by uvicorn;
# run: uvicorn py.starlette_app:app
import os
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
app = Starlette(routes=[Mount("/", app=StaticFiles(directory=DATA))])
