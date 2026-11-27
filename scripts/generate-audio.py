"""Generate locally bundled audio from the pinned sources in fetch-models.py."""
import io
import json
from pathlib import Path
import subprocess
import sys
import wave

from scipy.io.wavfile import write as write_wav

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / '.build'
OUTPUT = ROOT / 'web/audio'

def claude():
    sys.path.insert(0, str(BUILD / 'claude'))
    import torch
    from inference import get_text
    from models import SynthesizerTrn
    from text.symbols import symbols
    from utils import get_hparams_from_file, load_checkpoint

    torch.set_num_threads(3)
    torch.manual_seed(42)
    hps = get_hparams_from_file(str(BUILD / 'claude/config.json'))
    channels = hps.data.n_mel_channels if getattr(hps.model, 'use_mel_posterior_encoder', False) else hps.data.filter_length // 2 + 1
    model = SynthesizerTrn(len(symbols), channels, hps.train.segment_size // hps.data.hop_length,
                           n_speakers=hps.data.n_speakers, **hps.model)
    load_checkpoint(str(BUILD / 'claude/vits2-claude.pth'), model, None)
    model.eval()

    def speak(text):
        tokens = get_text(text.lower().replace('’', "'"), hps)
        with torch.inference_mode():
            samples = model.infer(tokens[None], torch.LongTensor([len(tokens)]),
                                  noise_scale=0.45, noise_scale_w=0.55, length_scale=1.04)[0][0, 0].numpy()
        data = io.BytesIO()
        write_wav(data, hps.data.sampling_rate, samples)
        return data.getvalue()
    return speak

def piper_voice(name):
    from piper import PiperVoice
    voice = PiperVoice.load(next(BUILD.rglob(name + '.onnx')))

    def speak(text):
        data = io.BytesIO()
        with wave.open(data, 'wb') as output:
            voice.synthesize_wav(text, output)
        return data.getvalue()
    return speak

def encode(name, wav):
    output = OUTPUT / (name + '.mp3')
    temp = output.with_suffix('.part.mp3')
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', 'pipe:0',
                    '-af', 'apad=pad_dur=0.18', '-ac', '1', '-b:a', '48k', str(temp)],
                   input=wav, check=True)
    temp.replace(output)

def generate(name, text, speak):
    forced = set(sys.argv[sys.argv.index('--force-scenes') + 1].split(',')) if '--force-scenes' in sys.argv else set()
    force_scene = any(name.startswith(scene_id + '-') for scene_id in forced)
    if '--missing' not in sys.argv or force_scene or not (OUTPUT / (name + '.mp3')).exists():
        encode(name, speak(text))

if __name__ == '__main__':
    OUTPUT.mkdir(exist_ok=True)
    selected_scene = sys.argv[sys.argv.index('--scene') + 1] if '--scene' in sys.argv else None
    if '--a1-expansion' in sys.argv:
        files = ['a1-expansion.json']
    elif '--a2-expansion' in sys.argv:
        files = ['a2-expansion.json']
    elif '--upper-expansion' in sys.argv:
        files = ['upper-expansion.json']
    else:
        files = ['scenes.json', 'itinerary.json', 'french.json', 'a1-expansion.json', 'a2-expansion.json']
    scenes = [scene for file in files for scene in json.loads((ROOT / 'content' / file).read_text())]
    if selected_scene:
        scenes = [scene for scene in scenes if scene['id'] == selected_scene]
        if not scenes:
            raise SystemExit(f'Unknown scene: {selected_scene}')
    field = json.loads((ROOT / 'web/field-data.json').read_text())
    voices = {
        'lb': claude,
        'da': lambda: piper_voice('da_DK-talesyntese-medium'),
        'fr': lambda: piper_voice('fr_FR-siwis-medium'),
    }
    lines = []
    for scene in scenes:
        for index, line in enumerate(scene['dialogue']):
            lines.append((f"{scene['id']}-line-{index}", line['text'], line.get('lang') or scene['lang']))
        for index, turn in enumerate(scene['turns']):
            for part in ['prompt', 'model']:
                lines.append((f"{scene['id']}-{part}-{index}", turn[part], scene['lang']))
        for index, line in enumerate((scene.get('enrichment') or {}).get('dialogue', [])):
            lines.append((f"{scene['id']}-line2-{index}", line['text'], scene['lang']))
        if scene.get('editorial_status') and scene.get('reading'):
            lines.append((f"{scene['id']}-reading-0", scene['reading']['text'], scene['lang']))
    for case in ([] if selected_scene else field['cases']):
        for line in [case['opening'], case['repair'], case['clarify'], *(slot['line'] for group in case['variants'] for slot in group)]:
            lines.append((line['audio'].split('/audio/', 1)[1].removesuffix('.mp3'), line['text'], line['lang']))
    for check in ([] if selected_scene else field['checks']):
        line = check['listening']['line']
        lines.append((line['audio'].split('/audio/', 1)[1].removesuffix('.mp3'), line['text'], line['lang']))
    (OUTPUT / 'field').mkdir(exist_ok=True)
    languages = [arg for arg in sys.argv[1:] if arg in voices]
    for lang, engine in voices.items():
        if languages and lang not in languages:
            continue
        speak = engine()
        for name, text, code in lines:
            if code == lang:
                generate(name, text, speak)
        print(lang, flush=True)
