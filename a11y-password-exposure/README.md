# a11y-password-exposure

Pilot for the paper *Masked on Screen, Plain on the Bus: What AT-SPI Exposes from Linux Password Fields to Accessibility-Tree Computer-Use Agents*.

**Question.** When a masked password field is read through AT-SPI (the Linux accessibility bus that computer-use agents use for their "accessibility tree" observation), does the plaintext reach the reader? And would the role-, name- and state-based redaction rules used by agent drivers catch it?

Everything is synthetic: fixture windows hold fake canary strings (`fixtures/canaries.json`). There are no real credentials, no personal data and no network calls.

## Requirements (Debian 13 "trixie", x86_64)
- System packages: `xvfb xfwm4 xdotool dbus python3-gi gir1.2-atspi-2.0 at-spi2-core gir1.2-gtk-3.0 gir1.2-gtk-4.0 firefox-esr`, plus Google Chrome.
- Alternatively, download the Debian 13 `.deb` files for at-spi2-core, gir1.2-atspi-2.0, gir1.2-atk-1.0, gir1.2-gtk-3.0, gir1.2-gtk-4.0, gir1.2-pango-1.0, gir1.2-harfbuzz-0.0, gir1.2-graphene-1.0, gir1.2-gdkpixbuf-2.0, gir1.2-freedesktop, firefox-esr and libevent-2.1-7t64. Extract each with `dpkg -x <deb> <prefix>`, and set `A11Y_ROOT=<prefix>` (no system install needed).

## Run (CPU only; about 100 s per repetition)
    ./env.sh            # Xvfb :97, isolated session bus, isolated a11y bus, at-spi2-registryd, org.a11y.Bus shim; one setsid process group
    source vars.sh
    python3 run_all.py gtk3 gtk4 chrome firefox --out results/rep1   # each fixture in its own process group, killed after reading
    python3 run_all.py gtk3 gtk4 chrome firefox --out results/rep2
    python3 analyze.py  # -> results/summary.json, results/summary.md
    ./teardown.sh       # kills only the env.sh process group

`run/` holds the browser profiles, sockets and logs of a run. It is not part of the published results.

## Files
- `env.sh`, `vars.sh`, `teardown.sh`, `bus_shim.py`: an isolated accessibility session. No system services are touched.
- `fixtures/`: GTK 3 and GTK 4 windows, and `form.html` for the browsers. Each has a plain "Username" field and two masked fields labelled "Password" and "Account key", filled programmatically.
  - GTK 3: two `Gtk.Entry` with visibility off.
  - GTK 4: one `Gtk.PasswordEntry` and one `Gtk.Entry` with visibility off.
  - Browsers: two `<input type=password>`.
- `reader.py`: an AT-SPI client (gi Atspi) standing in for an agent's observer.
  - Dumps role, name, description, states, interfaces, attributes, relations and Text.get_text for every node.
  - For each editable field after the first, it focuses the field (grab_focus, else click, else Tab), clears it, and types a fresh canary with xdotool.
  - While typing, it records text-changed, caret, name/description/value, selection and state events.
  - It scans everything for canaries, including keystroke-level inserts reassembled per source.
- `analyze.py`: for each masked field, reports plaintext in Text.get_text, plaintext in events, and three redaction rules:
  - `H_role`: role == "password text".
  - `H_orca`: a reimplementation of `is_secure_node` from stablyai/orca `native/computer-use-linux/runtime.py` at commit 24cebf03.
  - `H_orca_label`: H_orca plus the names of labelled-by targets.
- `results/rep1`, `results/rep2`: raw reader JSON for two repetitions. The browsers' address-bar text (the local path of `form.html`) is replaced by `<pilot-dir>`. `results/summary.{json,md}`: the summary. `results/screens/gtk4.png`: shows the GTK 4 fields rendered masked.
- `shot.py`: GDK screenshot helper (`python3 shot.py out.png` while a fixture is shown).

## Versions measured (2026-10-30)
- Debian 13 (trixie), Python 3.13.5, python3-gi 3.50.0.
- libatspi / at-spi2-core 2.56.2.
- GTK 3.24.49-3, GTK 4.18.6+ds-2.
- Google Chrome 156.0.8078.47 (`--force-renderer-accessibility`), Firefox ESR 140.15.0esr.
- Xvfb 21.1.16, xfwm4 4.20.0, xdotool 3.20160805.1.

## Result (rep1 == rep2)
See `results/summary.md`.
- **GTK 4.18.6:** returns the plaintext of both masked fields from Text.get_text and in text-changed events. The `Gtk.Entry` with visibility off has role "text", so none of the three redaction rules catches it. Upstream fixed this in GTK 4.19.2 and later (commits 49782b64 and c9e40e16).
- **GTK 3, Chrome and Firefox:** exposed mask characters only.
- `Atspi.StateType.PROTECTED` does not exist in libatspi 2.56.2.
- Masked text length equals secret length in 8 of 8 fields.

## License
MIT (see the repository LICENSE).
