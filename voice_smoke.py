"""Real Portuguese wake model and Silero endpoint smoke test with local test WAVs."""
import json
from pathlib import Path
import numpy as np
from vosk import Model, KaldiRecognizer, SetLogLevel
from faster_whisper.audio import decode_audio
from faster_whisper.vad import get_speech_timestamps, VadOptions
from voice_control import WAKE_PHRASES, SpeechEndpoint, wake_phrase_matches

ROOT=Path(__file__).resolve().parent
SetLogLevel(-1)
model=Model(str(ROOT/'models'/'vosk-model-small-pt-0.3'))
for filename, expected in [('wake-ok.wav',True),('wake-ola.wav',True),('wake-negative.wav',False)]:
    samples=decode_audio(str(ROOT/'.tmp'/filename))
    # Exercise the real microphone's 48 kHz sample rate as well as model endpointing.
    samples=np.interp(np.arange(0,len(samples),1/3),np.arange(len(samples)),samples).astype(np.float32)
    samples=np.concatenate([samples,np.zeros(48000,dtype=np.float32)])
    rec=KaldiRecognizer(model,48000,json.dumps([*WAKE_PHRASES,'[unk]'],ensure_ascii=False)); rec.SetWords(True)
    found=False
    for index in range(0,len(samples),4800):
        if rec.AcceptWaveform((samples[index:index+4800]*32767).astype('<i2').tobytes()):
            found=found or wake_phrase_matches(json.loads(rec.Result()))
    found=found or wake_phrase_matches(json.loads(rec.FinalResult()))
    assert found==expected,(filename,found)
    print('WAKE_OK',filename,found,flush=True)

audio=decode_audio(str(ROOT/'test-voice.wav'))
audio=np.concatenate([audio,np.zeros(16000*4,dtype=np.float32)])
endpoint=SpeechEndpoint(0,1.8); finished=None
for end in range(3200,len(audio),3200):
    tail=audio[max(0,end-16000):end]
    speech=get_speech_timestamps(tail,VadOptions(min_speech_duration_ms=100,min_silence_duration_ms=120,speech_pad_ms=0))
    recent=any(segment['end']>=len(tail)-2400 for segment in speech)
    if reason:=endpoint.update(end/16000,recent): finished=(end/16000,reason); break
assert finished and finished[1]=='silence',finished
print('AUTO_ENDPOINT_OK',finished,flush=True)
