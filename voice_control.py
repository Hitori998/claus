"""Offline wake detection and deterministic end-of-speech policy."""
import json
import queue
import re
import threading
import unicodedata

from PySide6.QtCore import QThread, Signal

WAKE_PHRASES = ('ok escuta', 'oi escuta', 'olá escuta', 'ei escuta')


def normalize(text):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFD', text.lower())
                           if not unicodedata.combining(c)).split())


def prepare_wake_phrase(value):
    phrase=' '.join(re.sub(r'[,;:.!?]', ' ', value.lower()).split())
    if not 1 <= len(phrase.split()) <= 4 or len(phrase)>60 or not all(c.isalpha() or c.isspace() for c in phrase):
        raise ValueError('Use de uma a quatro palavras em português, sem números ou símbolos.')
    return phrase


def wake_phrase_matches(result, phrases=WAKE_PHRASES):
    words = list(result.get('result', []))
    # Very short edge noise is sometimes decoded as [unk] before the actual call.
    while words and words[0].get('word') == '[unk]' and words[0].get('end', 1)-words[0].get('start', 0) <= 0.12: words.pop(0)
    while words and words[-1].get('word') == '[unk]' and words[-1].get('end', 1)-words[-1].get('start', 0) <= 0.12: words.pop()
    return (bool(words) and normalize(' '.join(w.get('word','') for w in words)) in {normalize(p) for p in phrases}
            and min(float(w.get('conf', 0)) for w in words) >= (0.92 if len(words)==1 else 0.72))


class SpeechEndpoint:
    def __init__(self, start, silence=1.8):
        self.start = start; self.last_speech = None; self.silence = silence

    def update(self, now, speech):
        if speech: self.last_speech = now
        if now - self.start >= 300: return 'limit'
        if self.last_speech is None:
            return 'no_speech' if now - self.start >= 10 else None
        return 'silence' if now - self.last_speech >= self.silence else None


class WakeListener(QThread):
    detected = Signal()
    ready = Signal()
    error = Signal(str)
    _model = None
    _model_lock = threading.Lock()

    def __init__(self, model_path, device, rate, phrases=WAKE_PHRASES):
        super().__init__(); self.model_path = model_path; self.device = device; self.rate = rate
        self.stopping = threading.Event(); self.audio = queue.Queue(maxsize=20)
        self.phrases=tuple(prepare_wake_phrase(phrase) for phrase in phrases)

    @classmethod
    def local_model(cls,path):
        with cls._model_lock:
            if cls._model is None:
                from vosk import Model,SetLogLevel
                SetLogLevel(-1); cls._model=Model(str(path))
        return cls._model

    @classmethod
    def validate_phrase(cls,path,phrase):
        phrase=prepare_wake_phrase(phrase)
        model=cls.local_model(path)
        missing=[word for word in phrase.split() if model.vosk_model_find_word(word)<0]
        if missing: raise ValueError('Palavra fora do vocabulário local: '+', '.join(missing)+'. Escolha outra chamada em português.')
        return phrase

    def stop(self): self.stopping.set()

    def callback(self, data, frames, time_info, status):
        if self.stopping.is_set(): return
        try: self.audio.put_nowait(bytes(data))
        except queue.Full: pass

    def run(self):
        try:
            import sounddevice as sd
            from vosk import KaldiRecognizer
            model=self.local_model(self.model_path)
            for phrase in self.phrases: self.validate_phrase(self.model_path,phrase)
            recognizer = KaldiRecognizer(model, self.rate,
                                        json.dumps([*self.phrases, '[unk]'], ensure_ascii=False))
            recognizer.SetWords(True)
            matched = False
            # Only the short call is recognized here; no idle audio is written to disk.
            with sd.RawInputStream(device=self.device, samplerate=self.rate, channels=1,
                                   dtype='int16', blocksize=round(self.rate * 0.1), callback=self.callback):
                self.ready.emit()
                while not self.stopping.is_set():
                    try: chunk = self.audio.get(timeout=0.15)
                    except queue.Empty: continue
                    if recognizer.AcceptWaveform(chunk) and wake_phrase_matches(json.loads(recognizer.Result()),self.phrases):
                        matched = True; break
            if matched and not self.stopping.is_set(): self.detected.emit()
        except Exception as exc:
            if not self.stopping.is_set(): self.error.emit(f'Ativação por voz indisponível: {exc}')
