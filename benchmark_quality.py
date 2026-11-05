"""Repeatable synthetic smoke benchmark; not a ranking for real microphones."""
import gc
import json
import re
import time
import unicodedata
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel
from faster_whisper.audio import decode_audio
from quality import model_options, model_path

ROOT = Path(__file__).resolve().parent
REFERENCE = 'Este é um teste de transcrição local. O aplicativo transforma áudio em texto sem usar serviços pagos.'


def tokens(text):
    text = ''.join(c for c in unicodedata.normalize('NFD', text.lower()) if not unicodedata.combining(c))
    return re.findall(r'\w+', text)


def wer(reference, hypothesis):
    ref, hyp = tokens(reference), tokens(hypothesis)
    row = list(range(len(hyp) + 1))
    for i, a in enumerate(ref, 1):
        next_row = [i]
        for j, b in enumerate(hyp, 1):
            next_row.append(min(next_row[-1] + 1, row[j] + 1, row[j-1] + (a != b)))
        row = next_row
    return round(row[-1] / max(1, len(ref)), 4)


audio = decode_audio(str(ROOT / 'test-voice.wav'))
rng = np.random.default_rng(41)
noise = rng.standard_normal(audio.shape).astype(np.float32)
noise *= np.sqrt(np.mean(audio ** 2)) / (10 ** (12 / 20))
variants = {'clean': audio, 'noise_12db': np.clip(audio + noise, -1, 1)}
results = []
for name in ['base', 'small', 'turbo']:
    model = WhisperModel(str(model_path(name)), device='cpu', compute_type='int8', cpu_threads=8,
                         local_files_only=True)
    for variant, samples in variants.items():
        start = time.monotonic()
        segments, _ = model.transcribe(samples, **model_options('pt'))
        text = ' '.join(segment.text.strip() for segment in segments)
        result = {'model': name, 'sample': variant, 'audio_seconds': round(len(samples)/16000, 2),
                  'processing_seconds': round(time.monotonic()-start, 2), 'wer': wer(REFERENCE, text), 'text': text}
        results.append(result)
        print(json.dumps(result, ensure_ascii=True), flush=True)
    del model
    gc.collect()
(ROOT / 'quality-benchmark.json').write_text(json.dumps({'reference': REFERENCE,
    'limitation': 'One synthetic Portuguese voice and deterministic added noise. Not a real-world accuracy guarantee.',
    'results': results}, ensure_ascii=False, indent=2), encoding='utf-8')
