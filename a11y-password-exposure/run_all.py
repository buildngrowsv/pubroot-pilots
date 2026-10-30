"""Launch each fixture in its own session/process group (start_new_session), read it with reader.py, then kill ONLY that group.
Usage: python3 run_all.py [gtk3 gtk4 chrome firefox] [--out results/repN]"""
import os, shutil, glob, subprocess, signal, sys, time
H = os.path.dirname(os.path.abspath(__file__)); R = os.environ.get("A11Y_ROOT", "")
args = sys.argv[1:]; OUT = f"{H}/results"
if "--out" in args: i = args.index("--out"); OUT = os.path.abspath(args[i + 1]); del args[i:i + 2]
os.makedirs(OUT, exist_ok=True)
FORM = f"file://{H}/fixtures/form.html"
FIREFOX = os.environ.get("FIREFOX", f"{R}/usr/lib/firefox-esr/firefox-esr")
FIX = {
 "gtk3":  (["python3", f"{H}/fixtures/gtk3_app.py"], "gtk3_app"),
 "gtk4":  (["python3", f"{H}/fixtures/gtk4_app.py"], "gtk4_app"),
 "chrome": (["google-chrome", "--force-renderer-accessibility", f"--user-data-dir={H}/run/chrome-profile", "--no-first-run",
             "--no-default-browser-check", "--disable-gpu", "--password-store=basic", "--disable-features=Translate", FORM], "chrome"),
 "firefox": ([FIREFOX, "-no-remote", "-profile", f"{H}/run/ff-profile", FORM], "firefox"),
}
which = args or list(FIX)
os.makedirs(f"{H}/run/fflib", exist_ok=True)  # libevent from an extracted .deb, if A11Y_ROOT is used
for so in glob.glob(f"{R}/usr/lib/x86_64-linux-gnu/libevent-2.1.so.7*") if R else []: shutil.copy(so, f"{H}/run/fflib/")
os.makedirs(f"{H}/run/ff-profile", exist_ok=True)
open(f"{H}/run/ff-profile/user.js", "w").write('user_pref("accessibility.force_disabled", -1);\nuser_pref("browser.shell.checkDefaultBrowser", false);\nuser_pref("datareporting.policy.dataSubmissionEnabled", false);\nuser_pref("toolkit.telemetry.reportingpolicy.firstRun", false);\nuser_pref("signon.rememberSignons", false);\n')
env = dict(os.environ, GNOME_ACCESSIBILITY="1", ACCESSIBILITY_ENABLED="1", MOZ_ENABLE_WAYLAND="0")
for f in which:
    cmd, name = FIX[f]
    log = open(f"{H}/run/{f}.log", "w")
    fenv = dict(env, LD_LIBRARY_PATH=f"{H}/run/fflib") if f == "firefox" else env
    p = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, env=fenv, start_new_session=True)
    time.sleep(12 if f in ("chrome", "firefox") else 4)
    try:
        subprocess.run(["python3", f"{H}/reader.py", name, f, f"{OUT}/{f}.json", "--type"], timeout=180, env=env)
    except subprocess.TimeoutExpired: print(f, "reader timeout")
    finally:
        try: os.killpg(p.pid, signal.SIGTERM); time.sleep(2); os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError: pass
    time.sleep(1)
