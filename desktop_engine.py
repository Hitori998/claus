import json
import logging
import os
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np
from quality import ROOT, model_path, model_options

GPU_EXE = ROOT / 'runtime' / 'vulkan' / 'whisper-cli.exe'
GPU_MODEL = ROOT / 'models' / 'ggml' / 'ggml-large-v3-turbo-q5_0.bin'


def paste_allowed(target, current, enabled):
    return bool(enabled and target and current == target)


def gpu_command(audio, output, language, glossary=''):
    args = [str(GPU_EXE), '-m', str(GPU_MODEL), '-f', str(audio), '-l', language,
            '-t', '8', '-nt', '-oj', '-of', str(output), '-tp', '0', '-nf', '-sns']
    if glossary.strip():
        args.extend(['--prompt', glossary.strip()])
    return args


class DictationEngine:
    def __init__(self):
        self.cpu_model = None
        self.cpu_name = None

    def transcribe(self, audio, backend='gpu', language='pt', glossary=''):
        from faster_whisper.audio import decode_audio
        from faster_whisper.vad import get_speech_timestamps, VadOptions
        samples = decode_audio(str(audio))
        if not get_speech_timestamps(samples, VadOptions(min_silence_duration_ms=600)):
            return ''
        if backend == 'gpu':
            if not GPU_EXE.is_file() or not GPU_MODEL.is_file():
                raise RuntimeError('Runtime ou modelo Vulkan ausente. Selecione CPU nas configurações.')
            with tempfile.TemporaryDirectory(dir=ROOT / '.tmp') as folder:
                wav = Path(folder) / 'speech.wav'
                with wave.open(str(wav), 'wb') as target:
                    target.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
                    target.writeframes((np.clip(samples, -1, 1) * 32767).astype('<i2').tobytes())
                output = Path(folder) / 'result'
                result = subprocess.run(gpu_command(wav, output, language, glossary), capture_output=True,
                                        creationflags=subprocess.CREATE_NO_WINDOW, timeout=300,
                                        env={**os.environ, 'VK_LOADER_LAYERS_DISABLE': '~implicit~'})
                if result.returncode != 0:
                    logging.error('Runtime Vulkan: %s', result.stderr.decode('utf-8', errors='replace')[-4000:])
                    raise RuntimeError('Falha no runtime Vulkan. Confira desktop.log ou selecione CPU.')
                data = json.loads(output.with_suffix('.json').read_text(encoding='utf-8'))
                return ' '.join(part['text'].strip() for part in data.get('transcription', []))
        if backend not in {'small', 'turbo'}:
            raise ValueError('Motor inválido.')
        if self.cpu_name != backend:
            from faster_whisper import WhisperModel
            self.cpu_model = None
            self.cpu_model = WhisperModel(str(model_path(backend)), device='cpu', compute_type='int8',
                                         cpu_threads=8, local_files_only=True)
            self.cpu_name = backend
        segments, _ = self.cpu_model.transcribe(samples, **model_options(language, glossary=glossary))
        return ' '.join(segment.text.strip() for segment in segments)
