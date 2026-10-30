# GTK 3 fixture: plain entry + two masked Gtk.Entry (visibility=False); synthetic canaries only.
import json, os, gi; gi.require_version("Gtk", "3.0"); from gi.repository import Gtk
C = json.load(open(os.path.join(os.path.dirname(__file__), "canaries.json")))
w = Gtk.Window(title="fixture-gtk3"); g = Gtk.Grid(row_spacing=6, column_spacing=6); w.add(g)
def row(i, label, text, masked):
    l = Gtk.Label(label=label); e = Gtk.Entry(); l.set_mnemonic_widget(e); e.set_visibility(not masked); e.set_text(text)
    g.attach(l, 0, i, 1, 1); g.attach(e, 1, i, 1, 1); return e
row(0, "Username", C["user"], False); row(1, "Password", C["pw"], True); row(2, "Account key", C["ak"], True)
w.connect("destroy", Gtk.main_quit); w.set_default_size(400, 160); w.show_all(); Gtk.main()
