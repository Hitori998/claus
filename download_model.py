import os
import argparse
from pathlib import Path

os.environ['HF_HUB_DISABLE_XET'] = '1'
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
from huggingface_hub import snapshot_download

from quality import MODEL_SPECS, model_path
parser = argparse.ArgumentParser()
parser.add_argument('models', nargs='*', default=['small', 'turbo'], choices=MODEL_SPECS)
args = parser.parse_args()
from faster_whisper import WhisperModel
for name in args.models:
    path = snapshot_download(MODEL_SPECS[name]['repo'], local_dir=model_path(name),
                            allow_patterns=['model.bin', 'config.json', 'tokenizer.json',
                                            'vocabulary.*', 'preprocessor_config.json'])
    model = WhisperModel(path, device='cpu', compute_type='int8', local_files_only=True)
    print(f'MODELO_LOCAL_OK {name}', flush=True)
    del model
