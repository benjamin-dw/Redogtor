# PyInstaller recipe for the Redactor desktop app.
#
#   pyinstaller build.spec
#
# Set the model before building if you want the smaller one:
#   MODEL=en_core_web_sm pyinstaller build.spec

import os

from PyInstaller.utils.hooks import collect_all, collect_data_files

MODEL = os.environ.get("MODEL", "en_core_web_lg")

datas, binaries, hiddenimports = [], [], []

# Everything spaCy, Presidio and the language model need at runtime.
for package in (
    MODEL,
    "spacy",
    "thinc",
    "blis",
    "cymem",
    "preshed",
    "murmurhash",
    "srsly",
    "catalogue",
    "wasabi",
    "confection",
    "presidio_analyzer",
    "presidio_anonymizer",
    "phonenumbers",
):
    try:
        d, b, h = collect_all(package)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

datas += collect_data_files("reportlab")
hiddenimports += [
    "spacy.lang.en",
    "spacy.pipeline",
    "srsly.msgpack.util",
    "waitress",
    "docx",
    "pypdf",
    MODEL,
]

a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "pytest", "IPython", "notebook"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Redactor",
    debug=False,
    strip=False,
    upx=False,
    console=True,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="Redactor",
)

app = BUNDLE(
    coll,
    name="Redactor.app",
    icon=None,
    bundle_identifier="ca.donatowoodger.redactor",
    info_plist={
        "CFBundleShortVersionString": "1.0.0",
        "LSUIElement": False,
        "NSHighResolutionCapable": True,
    },
)
