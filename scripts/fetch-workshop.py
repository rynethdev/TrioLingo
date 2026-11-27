"""Fetch and transcode the credited human recordings in the pronunciation catalogue."""
import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parent.parent
content = json.loads((root / 'web/field-data.json').read_text())
seen = set()
for drill in content['workshop']:
    for clip in drill['clips']:
        name = clip['audio'].rsplit('/', 1)[-1]
        target = root / 'web/audio/field' / name
        if name in seen or target.exists():
            continue
        seen.add(name)
        target.parent.mkdir(parents=True, exist_ok=True)
        response = subprocess.check_output(['curl', '-fsSL', '--retry', '2', '--max-time', '45',
                                            '-A', 'IdiomasLocal/1.0 educational desktop app', clip['download']])
        temp = target.with_suffix('.part.mp3')
        subprocess.run(['ffmpeg', '-nostdin', '-loglevel', 'error', '-y', '-i', 'pipe:0',
                        '-b:a', '96k', str(temp)], input=response, check=True)
        temp.replace(target)
        print(name, flush=True)
