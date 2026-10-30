# Screenshot of display :97 via GDK (visual check that fixture fields render masked). Usage: shot.py out.png
import sys, gi; gi.require_version("Gdk", "3.0"); from gi.repository import Gdk
w = Gdk.get_default_root_window(); pb = Gdk.pixbuf_get_from_window(w, 450, 350, 700, 300); pb.savev(sys.argv[1], "png", [], [])
