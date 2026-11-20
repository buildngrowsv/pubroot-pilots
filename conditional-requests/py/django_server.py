# Django django.views.static.serve (the view behind django.conf.urls.static) as a WSGI app on werkzeug's server, 127.0.0.1:PORT
import os, sys, logging
from django.conf import settings
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
settings.configure(DEBUG=False, ROOT_URLCONF=__name__, ALLOWED_HOSTS=["*"], SECRET_KEY=os.urandom(16).hex(), MIDDLEWARE=[])  # throwaway key; the static view does not use it
from django.urls import re_path
from django.views.static import serve
urlpatterns = [re_path(r"^(?P<path>.*)$", serve, {"document_root": DATA})]
from django.core.wsgi import get_wsgi_application
from werkzeug.serving import run_simple
logging.getLogger("werkzeug").setLevel(logging.ERROR)
run_simple("127.0.0.1", int(sys.argv[1]), get_wsgi_application())
