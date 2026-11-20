# Werkzeug send_file(conditional=True) (the path Flask's send_file uses) on werkzeug's dev server, 127.0.0.1:PORT
import os, sys, logging
from werkzeug.wrappers import Request
from werkzeug.utils import send_file
from werkzeug.serving import run_simple
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
@Request.application
def app(request): return send_file(os.path.join(DATA, request.path.lstrip("/")), request.environ, conditional=True)
logging.getLogger("werkzeug").setLevel(logging.ERROR)
run_simple("127.0.0.1", int(sys.argv[1]), app)
