import os
import tempfile
import threading
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from quality import MODEL_SPECS, model_path, model_options

ROOT = Path(__file__).resolve().parent
TEMP = ROOT / '.tmp'
TEMP.mkdir(exist_ok=True)
tempfile.tempdir = str(TEMP)
LIMIT = 500 * 1024 * 1024
EXTENSIONS = {'.wav', '.mp3', '.m4a', '.mp4', '.ogg', '.flac', '.webm', '.aac', '.wma', '.opus'}
LANGUAGES = {'pt', 'en', 'es', 'fr', 'de', 'ja', 'auto'}
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
jobs = {}
guard = threading.Lock()
model = None
loaded_model = None


def timestamp(seconds):
    milliseconds = max(0, round(seconds * 1000))
    seconds, ms = divmod(milliseconds, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f'{hours:02d}:{minutes:02d}:{seconds:02d},{ms:03d}'


def srt(segments):
    return '\n'.join(f"{i}\n{timestamp(s['start'])} --> {timestamp(s['end'])}\n{s['text'].strip()}\n"
                     for i, s in enumerate(segments, 1))


@app.middleware('http')
async def local_only(request: Request, call_next):
    if request.url.hostname not in {'127.0.0.1', 'localhost', 'testserver'}:
        return JSONResponse({'detail': 'Acesso somente pelo computador local.'}, status_code=403)
    if request.method not in {'GET', 'HEAD'}:
        origin = request.headers.get('origin')
        if request.headers.get('x-local-app') != '1' or (origin and origin not in
                {'http://127.0.0.1:8766', 'http://localhost:8766'}):
            return JSONResponse({'detail': 'Origem não autorizada.'}, status_code=403)
        length = request.headers.get('content-length')
        if length is None or not length.isdigit():
            return JSONResponse({'detail': 'Tamanho do arquivo obrigatório.'}, status_code=411)
        if int(length) > LIMIT + 1024 * 1024:
            return JSONResponse({'detail': 'Limite de 500 MB excedido.'}, status_code=413)
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; media-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'; object-src 'none'"
    response.headers['Cache-Control'] = 'no-store'
    return response


@app.get('/')
def index():
    return FileResponse(ROOT / 'static' / 'index.html')


@app.get('/api/health')
def health():
    available = [name for name in MODEL_SPECS if (model_path(name) / 'model.bin').is_file()]
    return {'app': 'escuta-local', 'ready': all(name in available for name in ['small', 'turbo']),
            'models': available, 'model': 'Whisper Small + Large v3 Turbo', 'device': 'CPU int8'}


@app.post('/api/shutdown')
def shutdown():
    with guard:
        if any(job['status'] == 'running' for job in jobs.values()):
            raise HTTPException(409, 'Aguarde a transcrição terminar antes de encerrar.')
    server = getattr(app.state, 'server', None)
    if server is not None:
        server.should_exit = True
    return {'message': 'Motor encerrado.'}


def transcribe(job_id, path, language, model_name, live, glossary):
    global model, loaded_model
    try:
        with guard:
            jobs[job_id]['message'] = 'Carregando motor local…'
        if model is None or loaded_model != model_name:
            import gc
            from faster_whisper import WhisperModel
            model = None
            gc.collect()
            model = WhisperModel(str(model_path(model_name)), device='cpu', compute_type='int8',
                                 cpu_threads=min(8, max(1, (os.cpu_count() or 2) - 1)),
                                 local_files_only=True)
            loaded_model = model_name
        segments, info = model.transcribe(str(path), **model_options(language, live, glossary))
        with guard:
            jobs[job_id].update(duration=info.duration, language=info.language, message='Reconhecendo fala…')
        for segment in segments:
            with guard:
                job = jobs[job_id]
                job['segments'].append({'start': segment.start, 'end': segment.end, 'text': segment.text.strip()})
                if live:
                    job['words'].extend({'start': w.start, 'end': w.end, 'text': w.word.strip()} for w in (segment.words or []))
                job['progress'] = min(99, round(segment.end / max(info.duration, 1) * 100))
        with guard:
            jobs[job_id].update(status='done', progress=100, message='Transcrição concluída. Revise o texto.'
                                if jobs[job_id]['segments'] else 'Nenhuma fala detectada neste arquivo.')
    except Exception as exc:
        with guard:
            jobs[job_id].update(status='error', message=f'Não foi possível transcrever. Confira o áudio e o modelo local. ({type(exc).__name__}: {str(exc)[:180]})')
    finally:
        path.unlink(missing_ok=True)


@app.post('/api/jobs')
def create_job(file: UploadFile = File(...), language: str = Form('pt'),
               model_name: str = Form('turbo'), live: bool = Form(False), glossary: str = Form('')):
    suffix = Path(file.filename or '').suffix.lower()
    if suffix not in EXTENSIONS or language not in LANGUAGES or model_name not in MODEL_SPECS or len(glossary) > 500:
        file.file.close()
        raise HTTPException(400, 'Selecione um formato de áudio válido e confira o idioma.')
    job_id = uuid.uuid4().hex
    path = TEMP / f'{job_id}{suffix}'
    with guard:
        if any(j['status'] == 'running' for j in jobs.values()):
            file.file.close()
            raise HTTPException(409, 'Uma transcrição está em andamento. Aguarde a conclusão.')
        # Results live in memory only, limited to ten jobs per server session.
        while len(jobs) >= 10:
            del jobs[next(iter(jobs))]
        jobs[job_id] = {'status': 'running', 'progress': 0, 'message': 'Preparando áudio…', 'segments': [],
                        'words': [], 'model': MODEL_SPECS[model_name]['name']}
    try:
        size = 0
        with path.open('wb') as target:
            while chunk := file.file.read(1024 * 1024):
                size += len(chunk)
                if size > LIMIT:
                    raise HTTPException(413, 'Limite de 500 MB excedido.')
                target.write(chunk)
        if not size:
            raise HTTPException(400, 'O arquivo está vazio.')
        if not (model_path(model_name) / 'model.bin').is_file():
            raise HTTPException(503, 'Modelo não instalado. Execute INSTALAR.cmd na pasta do aplicativo.')
        threading.Thread(target=transcribe, args=(job_id, path, language, model_name, live, glossary), daemon=True).start()
        return {'id': job_id}
    except Exception:
        path.unlink(missing_ok=True)
        with guard:
            jobs.pop(job_id, None)
        raise
    finally:
        file.file.close()


@app.get('/api/jobs/{job_id}')
def get_job(job_id: str):
    with guard:
        if job_id not in jobs:
            raise HTTPException(404, 'Transcrição não encontrada.')
        return {**jobs[job_id], 'segments': [dict(s) for s in jobs[job_id]['segments']],
                'words': [dict(w) for w in jobs[job_id]['words']]}


app.mount('/static', StaticFiles(directory=ROOT / 'static'), name='static')

if __name__ == '__main__':
    import uvicorn
    server = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=8766))
    app.state.server = server
    server.run()
