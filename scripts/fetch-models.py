"""Fetch the source material needed to build the optional speech packs and clips."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess

SOURCES = [
    ('ZLSCompLing/VITS2-Claude', '98aa56d700b14c29c415fbdc847aeed5f0cf3e5c', 'claude',
     'attentions.py commons.py config.json inference.py mel_processing.py models.py modules.py '
     'monotonic_align/__init__.py monotonic_align/core.pyx monotonic_align/setup.py '
     'text/__init__.py text/cleaners.py text/symbols.py transforms.py utils.py vits2-claude.pth'),
    ('unilux/whisper-base-v1-luxembourgish', 'e789d8e', 'lux',
     'added_tokens.json config.json model.safetensors vocab.json'),
    ('rhasspy/piper-voices', 'main', 'piper',
     'da/da_DK/talesyntese/medium/da_DK-talesyntese-medium.onnx '
     'da/da_DK/talesyntese/medium/da_DK-talesyntese-medium.onnx.json'),
    ('thorhojhus/whisper-small-danish', '5738a59229a5ef2a40180818860c93730568d98e', 'da-special',
     'added_tokens.json config.json model.safetensors vocab.json THIRD_PARTY_NOTICES.md'),
]

def fetch(item):
    repo, rev, folder, file = item
    target = Path('.build', folder, file)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        temp = target.with_suffix(target.suffix + '.part')
        subprocess.run(['curl', '-4', '-fsSL', '--retry', '2', '--max-time', '180',
                        f'https://huggingface.co/{repo}/resolve/{rev}/{file}?download=true',
                        '-o', str(temp)], check=True)
        temp.replace(target)
    print(target, flush=True)

if __name__ == '__main__':
    items = [(repo, rev, folder, file) for repo, rev, folder, files in SOURCES for file in files.split()]
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(fetch, items))
