import unittest
import tempfile
import wave
from pathlib import Path
from fastapi.testclient import TestClient
from app import app, srt, timestamp


class AppTests(unittest.TestCase):
    def test_audio_decoder_compatibility(self):
        from faster_whisper.audio import decode_audio
        with tempfile.TemporaryDirectory() as folder:
            filename = str(Path(folder) / 'silence.wav')
            with wave.open(filename, 'wb') as audio:
                audio.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
                audio.writeframes(b'\0\0' * 16000)
            self.assertEqual(len(decode_audio(filename)), 16000)

    def test_srt_rounds_and_preserves_unicode(self):
        self.assertEqual(timestamp(59.9996), '00:01:00,000')
        self.assertEqual(srt([{'start': 0, 'end': 1.25, 'text': 'Olá, avião!'}]),
                         '1\n00:00:00,000 --> 00:00:01,250\nOlá, avião!\n')

    def test_upload_requires_local_header(self):
        with TestClient(app) as client:
            self.assertEqual(client.post('/api/jobs').status_code, 403)

    def test_invalid_and_empty_file_rejected(self):
        with TestClient(app) as client:
            for name, data in [('arquivo.exe', b'bad'), ('vazio.wav', b'')]:
                response = client.post('/api/jobs', headers={'X-Local-App': '1'},
                                       files={'file': (name, data)}, data={'language': 'pt'})
                self.assertEqual(response.status_code, 400)

    def test_cross_origin_rejected(self):
        with TestClient(app) as client:
            response = client.post('/api/jobs', headers={'X-Local-App': '1', 'Origin': 'https://example.com'})
            self.assertEqual(response.status_code, 403)

    def test_unknown_job(self):
        with TestClient(app) as client:
            self.assertEqual(client.get('/api/jobs/missing').status_code, 404)


if __name__ == '__main__':
    unittest.main()
