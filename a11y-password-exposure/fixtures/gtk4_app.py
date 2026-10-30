# GTK 4 fixture: plain entry, Gtk.PasswordEntry, and a Gtk.Entry with visibility=False; synthetic canaries only.
import json, os, gi; gi.require_version("Gtk", "4.0"); from gi.repository import Gtk, GLib
GLib.set_prgname("gtk4_app"); GLib.set_application_name("gtk4_app")
C = json.load(open(os.path.join(os.path.dirname(__file__), "canaries.json")))
def act(app):
    w = Gtk.ApplicationWindow(application=app, title="fixture-gtk4"); g = Gtk.Grid(row_spacing=6, column_spacing=6); w.set_child(g)
    def row(i, label, e, text):
        l = Gtk.Label(label=label); l.set_mnemonic_widget(e); e.set_text(text)
        g.attach(l, 0, i, 1, 1); g.attach(e, 1, i, 1, 1)
    row(0, "Username", Gtk.Entry(), C["user"])
    row(1, "Password", Gtk.PasswordEntry(), C["pw"])
    e = Gtk.Entry(); e.set_visibility(False); row(2, "Account key", e, C["ak"])
    w.set_default_size(400, 160); w.present()
app = Gtk.Application(application_id="org.pilot.fixturegtk4"); app.connect("activate", act); app.run([])
