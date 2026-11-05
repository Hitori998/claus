"""Real local model + HTTP integration; run with the server already started."""
import io
import json
import subprocess
import time
import wave
from pathlib import Path

import httpx
from app import TEMP

ROOT = Path(__file__).resolve().parent
voice = ROOT / 'test-voice.wav'
assert voice.is_file(), 'Gere test-voice.wav com uma voz sintetica antes do teste.'
client = httpx.Client(base_url='http://127.0.0.1:8766', timeout=30)
assert client.get('/api/health').json()['ready']


def recognize(data, model_name='turbo', live=False):
    start = time.monotonic()
    response = client.post('/api/jobs', headers={'X-Local-App': '1'},
                           files={'file': ('teste.wav', data)},
                           data={'language': 'pt', 'model_name': model_name, 'live': str(live).lower()})
    response.raise_for_status()
    job_id = response.json()['id']
    while time.monotonic() - start < 90:
        job = client.get(f'/api/jobs/{job_id}').json()
        assert job['status'] != 'error', job
        if job['status'] == 'done':
            if live and job['segments']:
                assert job['words'], 'A previa ao vivo deve fornecer tempos por palavra.'
            assert not list(TEMP.glob(job_id + '.*')), 'Audio temporario nao foi removido.'
            return job, time.monotonic() - start
        time.sleep(0.2)
    raise AssertionError('Transcricao excedeu 90 segundos.')


job, elapsed = recognize(voice.read_bytes())
text = ' '.join(s['text'] for s in job['segments'])
assert 'transcri' in text.lower() and 'local' in text.lower(), text
print(f'ARQUIVO_OK {elapsed:.2f}s: {text}', flush=True)

# Feed overlapping windows and use the real browser merge code on their words.
with wave.open(str(voice), 'rb') as audio:
    params = audio.getparams()
    rate = audio.getframerate()
    hypotheses = []
    end = min(rate * 6, audio.getnframes())
    while True:
        offset = max(0, end - rate * 18)
        audio.setpos(offset)
        frames = audio.readframes(end - offset)
        output = io.BytesIO()
        with wave.open(output, 'wb') as chunk:
            chunk.setparams(params)
            chunk.writeframes(frames)
        job, elapsed = recognize(output.getvalue(), model_name='small', live=True)
        text = ' '.join(s['text'] for s in job['segments'])
        hypotheses.append({'offset': offset / rate, 'words': job['words']})
        print(f'TRECHO_AO_VIVO_OK {elapsed:.2f}s: {text}', flush=True)
        if end >= audio.getnframes():
            break
        end = min(end + rate * 6, audio.getnframes())
    script = "const {mergeWords,wordsToSegments}=require('./static/streaming.js');let data='';process.stdin.on('data',s=>data+=s);process.stdin.on('end',()=>{let words=[];for(const h of JSON.parse(data))words=mergeWords(words,h.words,h.offset);process.stdout.write(wordsToSegments(words).map(s=>s.text).join(' '));});"
    result = subprocess.run(['node', '-e', script], input=json.dumps(hypotheses), capture_output=True,
                            text=True, encoding='utf-8', check=True, cwd=ROOT)
    assert all(word in result.stdout.lower() for word in ['local', 'áudio', 'aplicativo']), result.stdout
    print('CONTEXTO_AO_VIVO_OK ' + result.stdout, flush=True)
client.close()
