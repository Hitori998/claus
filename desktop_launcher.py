"""Small native executable entrypoint; uses the app's installed portable runtime."""
import ctypes
from pathlib import Path
import subprocess
import sys

root = Path(sys.executable).parent / 'transcritor-local' if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
try:
    python = root / '.venv' / 'Scripts' / 'pythonw.exe'
    if not python.is_file(): raise RuntimeError('A pasta transcritor-local deve permanecer ao lado de Claus.exe.')
    with (root / 'desktop-launch.log').open('a', encoding='utf-8') as log:
        subprocess.Popen([str(python), str(root / 'desktop.py')], cwd=root,
                         stdout=log, stderr=log, stdin=subprocess.DEVNULL,
                         creationflags=subprocess.CREATE_NO_WINDOW)
except Exception as exc:
    ctypes.windll.user32.MessageBoxW(0,str(exc),'Claus — inicialização',0x10)
