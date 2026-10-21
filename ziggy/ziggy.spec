# -*- mode: python ; coding: utf-8 -*-
# Construction :  pyinstaller --noconfirm --clean ziggy.spec      (ou build.bat)
# Résultat : dist/Ziggy/  contenant
#   Ziggy.exe              application sans console (celle qu'on installe et qu'on lance)
#   Ziggy-diagnostic.exe   même programme AVEC console : sert à `--check` et au dépannage
import os, sys
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

WIN = sys.platform == "win32"
# Toujours travailler depuis le dossier où se trouve ce fichier .spec.
# GitHub Actions peut lancer PyInstaller depuis un autre dossier.
ROOT = os.path.dirname(os.path.abspath(SPEC)) if "SPEC" in globals() else os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

# Interface, icônes et modèle de configuration embarqués (lecture seule).
# Les chemins sources sont absolus pour éviter les erreurs de répertoire courant.
datas = []
for source, destination in (("static", "static"), ("assets", "assets")):
    if os.path.exists(os.path.join(ROOT, source)):
        datas.append((os.path.join(ROOT, source), destination))
    else:
        raise FileNotFoundError(f"Dossier requis pour compiler Ziggy introuvable : {os.path.join(ROOT, source)}")

example_env = os.path.join(ROOT, ".env.example")
if os.path.isfile(example_env):
    datas.append((example_env, "."))
else:
    # Ce modèle est facultatif : son absence ne doit pas empêcher la création du .exe.
    print(f"[spec] AVERTISSEMENT : .env.example absent ({example_env}); compilation sans ce modèle.")
binaries, hiddenimports = [], []

# Paquets qui chargent des fichiers/modules dynamiquement : embarqués en entier
for pkg in ("google.genai", "google.auth", "google.oauth2", "google_auth_oauthlib",
            "msal", "spotipy", "httplib2", "certifi", "waitress", "pystray"):
    try:
        d, b, h = collect_all(pkg)
        datas += d; binaries += b; hiddenimports += h
    except Exception as e:                                   # pystray peut manquer hors Windows
        print(f"[spec] {pkg} ignoré : {e}")

datas += collect_data_files("googleapiclient")               # descriptions d'API Gmail / Agenda / Drive
hiddenimports += collect_submodules("googleapiclient")
datas += collect_data_files("docx")                          # modèle Word par défaut
datas += collect_data_files("pptx")                          # modèle PowerPoint par défaut
hiddenimports += ["openpyxl", "pypdf", "pyperclip", "dotenv", "PIL.Image", "httpx",
                  "version", "paths", "logsetup", "secrets_store", "settings", "database", "gemini", "security",
                  "actions", "reminders", "system_integration", "selfcheck", "readers", "extras", "apps",
                  "telegram_bot", "google_services", "microsoft_services"]

ICON = os.path.join(ROOT, "assets", "ziggy.ico") if WIN and os.path.isfile(os.path.join(ROOT, "assets", "ziggy.ico")) else None   # icône personnalisée (lotus)
VERSION_FILE = None
if WIN:                                                       # métadonnées de l'exe (Propriétés > Détails)
    sys.path.insert(0, ROOT)
    from version import APP_VERSION
    t = tuple(int(x) for x in (APP_VERSION.split(".") + ["0"] * 4)[:4])
    os.makedirs("build", exist_ok=True)
    VERSION_FILE = os.path.join("build", "version_info.txt")
    with open(VERSION_FILE, "w", encoding="utf-8") as f:
        f.write(f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers={t}, prodvers={t}, mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[StringFileInfo([StringTable('040C04B0', [
    StringStruct('CompanyName', 'Solar'), StringStruct('FileDescription', 'Ziggy - assistant personnel'),
    StringStruct('FileVersion', '{APP_VERSION}'), StringStruct('InternalName', 'Ziggy'),
    StringStruct('OriginalFilename', 'Ziggy.exe'), StringStruct('ProductName', 'Ziggy'),
    StringStruct('ProductVersion', '{APP_VERSION}')])]), VarFileInfo([VarStruct('Translation', [1036, 1200])])])
""")

a = Analysis([os.path.join(ROOT, "ziggy.py")], pathex=[ROOT], binaries=binaries, datas=datas, hiddenimports=hiddenimports,
             excludes=["tkinter", "matplotlib", "numpy", "pandas", "scipy", "PIL.ImageTk", "IPython", "pytest"])
pyz = PYZ(a.pure)

exe_gui = EXE(pyz, a.scripts, [], exclude_binaries=True, name="Ziggy", console=False, icon=ICON, version=VERSION_FILE, upx=False)
exe_diag = EXE(pyz, a.scripts, [], exclude_binaries=True, name="Ziggy-diagnostic", console=True, icon=ICON, version=VERSION_FILE, upx=False)
coll = COLLECT(exe_gui, exe_diag, a.binaries, a.datas, name="Ziggy", upx=False)
