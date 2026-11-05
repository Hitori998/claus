"""Local model registry and decoding settings; never resolves remote models at runtime."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODEL_SPECS = {
    'base': {'name': 'Whisper Base', 'repo': 'Systran/faster-whisper-base'},
    'small': {'name': 'Whisper Small', 'repo': 'Systran/faster-whisper-small'},
    'turbo': {'name': 'Whisper Large v3 Turbo', 'repo': 'dropbox-dash/faster-whisper-large-v3-turbo'},
}


def model_path(name):
    if name not in MODEL_SPECS:
        raise ValueError('Modelo não permitido.')
    return ROOT / 'models' / name


def model_options(language, live=False, glossary=''):
    return dict(language=None if language == 'auto' else language,
                beam_size=5, temperature=0, vad_filter=True,
                vad_parameters={'min_silence_duration_ms': 650, 'speech_pad_ms': 350},
                condition_on_previous_text=not live, word_timestamps=live,
                hotwords=glossary.strip() or None)
