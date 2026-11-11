# Starlette FileResponse served by uvicorn; run: uvicorn py.starlette_app:app
import os
from starlette.applications import Starlette
from starlette.responses import FileResponse
from starlette.routing import Route
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
async def f(request): return FileResponse(os.path.join(DATA, request.path_params["name"]))
app = Starlette(routes=[Route("/{name}", f)])
