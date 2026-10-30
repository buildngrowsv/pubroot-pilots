# source me: environment for the fixture apps and the reader
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); ROOT=${A11Y_ROOT:-}
export DISPLAY=:97 DBUS_SESSION_BUS_ADDRESS=unix:path=$HERE/run/session.sock AT_SPI_BUS_ADDRESS=$(head -1 $HERE/run/a11y.addr)
[ -n "$ROOT" ] && export GI_TYPELIB_PATH=$ROOT/usr/lib/x86_64-linux-gnu/girepository-1.0
export NO_AT_BRIDGE=0 GTK_A11Y=atspi GSETTINGS_BACKEND=memory GDK_BACKEND=x11 LIBGL_ALWAYS_SOFTWARE=1
