#!/usr/bin/env python3
"""
Start Redogtor on Windows, macOS or Linux.

First run: sets everything up, which takes 10-25 minutes.
Later runs: starts in a few seconds.

    python3 run.py        (macOS, Linux)
    py run.py             (Windows)
"""

import os
import platform
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

HERE = Path(__file__).resolve().parent
VENV = HERE / ".venv"
READY = VENV / "ready.txt"
PORT = os.environ.get("REDACTOR_PORT", "8765")
WINDOWS = os.name == "nt"

WHEEL = ("https://github.com/explosion/spacy-models/releases/download/"
         "{m}-3.8.0/{m}-3.8.0-py3-none-any.whl")

PACKAGES = [
    "flask", "waitress", "spacy>=3.8,<3.9",
    "presidio-analyzer", "presidio-anonymizer",
    "python-docx", "pypdf", "reportlab",
]


def venv_python():
    return VENV / ("Scripts" if WINDOWS else "bin") / ("python.exe" if WINDOWS else "python")


def memory_mb():
    """Best effort. Returns 0 if it cannot tell."""
    try:
        if platform.system() == "Linux":
            for line in open("/proc/meminfo"):
                if line.startswith("MemTotal"):
                    return int(line.split()[1]) // 1024
        elif platform.system() == "Darwin":
            out = subprocess.check_output(["sysctl", "-n", "hw.memsize"])
            return int(out.strip()) // (1024 * 1024)
        elif WINDOWS:
            import ctypes

            class Status(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong),
                            ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong),
                            ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong),
                            ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong),
                            ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullExtendedVirtual", ctypes.c_ulonglong)]

            s = Status()
            s.dwLength = ctypes.sizeof(Status)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(s))
            return int(s.ullTotalPhys) // (1024 * 1024)
    except Exception:
        pass
    return 0


def run(cmd):
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print("\nThat step failed. The message above says why.")
        input("Press Enter to close.")
        sys.exit(1)


def setup():
    if sys.version_info < (3, 9):
        print("This needs Python 3.9 or newer. You have %s."
              % platform.python_version())
        input("Press Enter to close.")
        sys.exit(1)

    if not venv_python().exists():
        print("Creating a private folder for the program's parts...")
        made = subprocess.run([sys.executable, "-m", "venv", str(VENV)])
        if made.returncode != 0:
            print("\nCould not create it. On openSUSE run this, then try again:")
            print("   sudo zypper install python3-devel python3-pip")
            input("Press Enter to close.")
            sys.exit(1)

    py = str(venv_python())
    print("Installing. On a slow machine this takes 10 to 25 minutes.")
    run([py, "-m", "pip", "install", "-q", "--upgrade", "pip", "setuptools", "wheel"])
    run([py, "-m", "pip", "install", "-q"] + PACKAGES)

    ram = memory_mb()
    model = "en_core_web_lg" if ram >= 3000 else "en_core_web_sm"
    print("Memory found: %s MB. Using the %s language model."
          % (ram or "unknown", model))
    try:
        subprocess.run([py, "-m", "pip", "install", "-q", WHEEL.format(m=model)],
                       check=True)
    except subprocess.CalledProcessError:
        print("That model would not download. Falling back to the small one.")
        model = "en_core_web_sm"
        run([py, "-m", "pip", "install", "-q", WHEEL.format(m=model)])

    READY.write_text(model, encoding="utf-8")
    make_shortcut()
    return model


DESKTOP_ENTRY = """[Desktop Entry]
Type=Application
Name=Redogtor
Comment=Take identifying details out of a document
Exec={exe} {script}
Icon={icon}
Terminal=false
Categories=Utility;Office;
StartupNotify=true
"""


def make_shortcut():
    """Put a clickable Redogtor entry in the applications menu (Linux only)."""
    if platform.system() != "Linux":
        return
    import base64
    import re as _re

    apps = Path.home() / ".local/share/applications"
    icons = Path.home() / ".local/share/icons"
    try:
        apps.mkdir(parents=True, exist_ok=True)
        icons.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        print("Could not create the menu folders: %s" % exc)
        return

    # Icon, taken straight from app.py so changing it there is enough.
    icon = icons / "redogtor.png"
    try:
        src = (HERE / "app.py").read_text(encoding="utf-8")
        m = _re.search(r'ICON_512 = "([^"]+)"', src)
        if m:
            fresh = base64.b64decode(m.group(1))
            if not icon.exists() or icon.read_bytes() != fresh:
                icon.write_bytes(fresh)
    except Exception as exc:
        print("Could not write the icon (%s). Carrying on without it." % exc)

    exe = venv_python()
    script = HERE / "run.py"
    if not exe.exists() or not script.exists():
        print("Cannot make a menu entry: %s or %s is missing." % (exe, script))
        return

    entry = apps / "redogtor.desktop"
    try:
        entry.write_text(
            DESKTOP_ENTRY.format(
                exe=exe, script=script,
                icon=icon if icon.exists() else "utilities-terminal"),
            encoding="utf-8",
        )
        entry.chmod(0o755)
    except Exception as exc:
        print("Could not write the menu entry: %s" % exc)
        return

    # Only once the new one is safely in place.
    for stale in (apps / "redactor.desktop", icons / "redactor.png",
                  apps / "redogter.desktop", icons / "redogter.png"):
        try:
            stale.unlink()
        except FileNotFoundError:
            pass
        except Exception:
            pass

    for cmd in (["update-desktop-database", str(apps)],
                ["gtk-update-icon-cache", "-f", "-t", str(icons)]):
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            pass

    print("Menu entry ready: %s" % entry)


def wait_then_open(url):
    for _ in range(90):
        time.sleep(1)
        try:
            urllib.request.urlopen(url + "health", timeout=2)
            webbrowser.open(url)
            return
        except Exception:
            continue


def stop_old_copy():
    """An earlier copy still holding the port would block this one."""
    url = "http://127.0.0.1:%s/" % PORT
    try:
        urllib.request.urlopen(url + "health", timeout=2)
    except Exception:
        return True                      # nothing there, port is free

    print("An older copy of Redogtor is already running. Stopping it...")
    try:
        req = urllib.request.Request(url + "quit", data=b"", method="POST")
        urllib.request.urlopen(req, timeout=3)
    except Exception:
        pass

    for _ in range(15):
        time.sleep(1)
        try:
            urllib.request.urlopen(url + "health", timeout=2)
        except Exception:
            print("Stopped. Starting the new one.")
            return True

    print("\nCould not stop it. In a terminal, run:")
    print("   pkill -f %s" % (HERE / "app.py"))
    print("then start Redogtor again.")
    print("Or start this one on a different port:")
    print("   REDACTOR_PORT=8766 python3 run.py")
    input("Press Enter to close.")
    return False


def main():
    if READY.exists() and venv_python().exists():
        model = READY.read_text(encoding="utf-8").strip()
        print("Already set up. Starting...")
        make_shortcut()
    else:
        model = setup()

    env = dict(os.environ)
    env["REDACTOR_MODEL"] = model
    env["REDACTOR_PORT"] = PORT
    env["REDACTOR_HOST"] = os.environ.get("REDACTOR_HOST", "127.0.0.1")
    env["REDACTOR_DESKTOP"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    if not stop_old_copy():
        sys.exit(1)

    url = "http://127.0.0.1:%s/" % PORT
    print("\nStarting Redogtor. Your browser will open at %s" % url)
    print("The first document takes about 30 seconds.\n")

    try:
        subprocess.run([str(venv_python()), str(HERE / "app.py")], env=env)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
