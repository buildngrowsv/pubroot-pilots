# aiohttp web.FileResponse on 127.0.0.1:PORT
import os, sys
from aiohttp import web
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
async def f(request): return web.FileResponse(os.path.join(DATA, request.match_info["name"]))
app = web.Application(); app.router.add_get("/{name}", f)
web.run_app(app, host="127.0.0.1", port=int(sys.argv[1]), print=None)
