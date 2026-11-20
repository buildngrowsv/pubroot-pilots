# Tornado StaticFileHandler on 127.0.0.1:PORT
import os, sys, asyncio, logging
import tornado.web
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
logging.getLogger("tornado.access").setLevel(logging.ERROR)
async def main():
    tornado.web.Application([(r"/(.*)", tornado.web.StaticFileHandler, {"path": DATA})]).listen(int(sys.argv[1]), "127.0.0.1")
    await asyncio.Event().wait()
asyncio.run(main())
