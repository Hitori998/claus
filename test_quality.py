import unittest
from pathlib import Path
from quality import MODEL_SPECS, model_path, model_options


class QualityTests(unittest.TestCase):
    def test_model_paths_are_allowlisted(self):
        self.assertEqual(model_path('turbo').name, 'turbo')
        self.assertEqual(model_path('small').parent.name, 'models')
        with self.assertRaises(ValueError):
            model_path('../outside')

    def test_live_has_word_timestamps_and_deterministic_decode(self):
        options = model_options('pt', live=True, glossary='Botelho, transcrição')
        self.assertTrue(options['word_timestamps'])
        self.assertEqual(options['temperature'], 0)
        self.assertEqual(options['hotwords'], 'Botelho, transcrição')
        self.assertEqual(options['language'], 'pt')

    def test_files_keep_context_and_automatic_language(self):
        options = model_options('auto', live=False)
        self.assertIsNone(options['language'])
        self.assertTrue(options['condition_on_previous_text'])


if __name__ == '__main__':
    unittest.main()
