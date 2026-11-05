import ctypes
import json
import os
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
URL = 'http://127.0.0.1:8766'


def running():
    try:
        with urllib.request.urlopen(URL + '/api/health', timeout=1) as response:
            return json.load(response).get('app') == 'escuta-local'
    except Exception:
        return False


try:
    if not running():
        env = {**os.environ, 'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1',
               'HF_HUB_DISABLE_TELEMETRY': '1', 'DO_NOT_TRACK': '1',
               'TEMP': str(ROOT / '.tmp'), 'TMP': str(ROOT / '.tmp'),
               'HF_HOME': str(ROOT / 'models' / '.hf')}
        (ROOT / '.tmp').mkdir(exist_ok=True)
        with (ROOT / 'server.log').open('a', encoding='utf-8') as log:
            subprocess.Popen([str(ROOT / '.venv' / 'Scripts' / 'python.exe'), str(ROOT / 'app.py')],
                             cwd=ROOT, env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                             creationflags=subprocess.CREATE_NO_WINDOW)
        for _ in range(60):
            if running():
                break
            time.sleep(0.25)
        else:
            raise RuntimeError('O motor não iniciou. Consulte server.log ou execute INSTALAR.cmd.')
    if '--no-browser' not in sys.argv:
        webbrowser.open(URL)
    print('ESCUTA_PRONTO ' + URL)
except Exception as exc:
    ctypes.windll.user32.MessageBoxW(0, str(exc), 'Escuta — falha na inicialização', 0x10)
    raise
