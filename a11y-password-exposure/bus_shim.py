# Minimal stand-in for at-spi-bus-launcher's session-bus API: owns org.a11y.Bus on OUR isolated session bus,
# answers GetAddress with OUR isolated a11y bus, and reports org.a11y.Status IsEnabled/ScreenReaderEnabled = true.
import sys; from gi.repository import Gio, GLib
ADDR = open(sys.argv[1]).readline().strip()
XML = """<node><interface name='org.a11y.Bus'><method name='GetAddress'><arg type='s' direction='out'/></method></interface>
<interface name='org.a11y.Status'><property name='IsEnabled' type='b' access='readwrite'/><property name='ScreenReaderEnabled' type='b' access='readwrite'/></interface></node>"""
node = Gio.DBusNodeInfo.new_for_xml(XML)
def call(c, s, p, i, m, params, inv): inv.return_value(GLib.Variant("(s)", (ADDR,)))
def getp(c, s, p, i, prop): return GLib.Variant("b", True)
def acquired(conn, name):
    conn.register_object("/org/a11y/bus", node.interfaces[0], call, None, None)
    conn.register_object("/org/a11y/bus", node.interfaces[1], None, getp, lambda *a: True)
Gio.bus_own_name(Gio.BusType.SESSION, "org.a11y.Bus", 0, acquired, None, None)
GLib.MainLoop().run()
