#!/usr/bin/env bash
# Isolated, self-contained accessibility session for the pilot. Starts ONLY this pilot's own processes in one process
# group (setsid) on display :97, with isolated D-Bus buses under ./run/. teardown.sh kills only that process group.
# A11Y_ROOT: prefix holding at-spi2-core 2.56.2 (usr/libexec/at-spi2-registryd, usr/share/defaults/at-spi2/accessibility.conf).
#   Leave it unset on a Debian 13 system with at-spi2-core installed, or point it at a folder of Debian 13 .debs
#   extracted with `dpkg -x` (see README).
set -e
HERE=$(cd "$(dirname "$0")" && pwd); RUN=$HERE/run; ROOT=${A11Y_ROOT:-}
mkdir -p $RUN/svc
cat > $RUN/svc/org.a11y.atspi.Registry.service <<S
[D-BUS Service]
Name=org.a11y.atspi.Registry
Exec=$ROOT/usr/libexec/at-spi2-registryd --use-gnome-session=false
S
sed -e "s#<servicedir>.*</servicedir>#<servicedir>$RUN/svc</servicedir>#" -e "s#unix:dir=/tmp#unix:dir=$RUN#" \
    $ROOT/usr/share/defaults/at-spi2/accessibility.conf > $RUN/a11y.conf
cat > $RUN/start.sh <<S
#!/usr/bin/env bash
Xvfb :97 -screen 0 1600x1000x24 -nolisten tcp >$RUN/xvfb.log 2>&1 &
dbus-daemon --session --nofork --address=unix:path=$RUN/session.sock >$RUN/session.log 2>&1 &
dbus-daemon --config-file=$RUN/a11y.conf --nofork --print-address=3 3>$RUN/a11y.addr >$RUN/a11y.log 2>&1 &
sleep 1.5
export DBUS_SESSION_BUS_ADDRESS=unix:path=$RUN/session.sock
AT_SPI_BUS_ADDRESS=\$(head -1 $RUN/a11y.addr) $ROOT/usr/libexec/at-spi2-registryd --use-gnome-session=false >$RUN/registryd.log 2>&1 &
python3 $HERE/bus_shim.py $RUN/a11y.addr >$RUN/shim.log 2>&1 &
DISPLAY=:97 xfwm4 --compositor=off >$RUN/wm.log 2>&1 &
wait
S
chmod +x $RUN/start.sh
setsid $RUN/start.sh >/dev/null 2>&1 < /dev/null &
sleep 3
PGID=$(ps -o pgid= -p $(pgrep -f "$RUN/start.sh" | head -1) | tr -d ' '); echo $PGID > $RUN/pgid
echo "pgid $PGID  a11y $(cat $RUN/a11y.addr)"
