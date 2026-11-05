import unittest
from voice_control import SpeechEndpoint, wake_phrase_matches, prepare_wake_phrase


class VoiceControlTests(unittest.TestCase):
    def test_custom_single_word_and_phrase_are_exact_and_confident(self):
        result={'text':'computador','result':[{'word':'computador','conf':0.98}]}
        self.assertTrue(wake_phrase_matches(result,('computador',)))
        self.assertFalse(wake_phrase_matches(result,('ok escuta',)))
        result['result'][0]['conf']=0.8
        self.assertFalse(wake_phrase_matches(result,('computador',)))
        self.assertEqual(prepare_wake_phrase('  Ok,   Escuta! '),'ok escuta')
        for invalid in ('','123','[unk]','uma frase que tem cinco palavras'):
            with self.assertRaises(ValueError): prepare_wake_phrase(invalid)
    def test_wake_phrase_requires_two_words_and_confidence(self):
        def result(text, confidence=0.9):
            return {'text': text, 'result': [{'word':word,'conf':confidence} for word in text.split()]}
        self.assertTrue(wake_phrase_matches(result('ok escuta')))
        self.assertTrue(wake_phrase_matches(result('olá escuta')))
        self.assertFalse(wake_phrase_matches(result('escuta')))
        self.assertFalse(wake_phrase_matches(result('ok escuta',0.35)))
        self.assertFalse(wake_phrase_matches(result('quero escutar música')))
        self.assertFalse(wake_phrase_matches(result('oi [unk] escuta')))
        edge = result('ok escuta'); edge['result'].insert(0,{'word':'[unk]','conf':0.9,'start':0,'end':0.06})
        self.assertTrue(wake_phrase_matches(edge))

    def test_stops_after_speech_and_pause_without_a_key(self):
        endpoint = SpeechEndpoint(start=0, silence=1.8)
        self.assertIsNone(endpoint.update(0.2, False))
        self.assertIsNone(endpoint.update(1, True))
        self.assertIsNone(endpoint.update(2.5, False))
        self.assertEqual(endpoint.update(2.9, False), 'silence')

    def test_a_short_pause_does_not_end_the_utterance(self):
        endpoint = SpeechEndpoint(start=0, silence=1.8)
        endpoint.update(1,True)
        self.assertIsNone(endpoint.update(2,False))
        endpoint.update(2.1,True)
        self.assertIsNone(endpoint.update(3.5,False))
        self.assertEqual(endpoint.update(4,False),'silence')

    def test_no_speech_times_out_and_long_speech_is_bounded(self):
        self.assertEqual(SpeechEndpoint(start=0).update(10.1,False),'no_speech')
        self.assertEqual(SpeechEndpoint(start=0).update(300.1,True),'limit')


if __name__ == '__main__': unittest.main()
