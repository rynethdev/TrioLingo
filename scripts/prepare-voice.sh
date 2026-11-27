#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
voice_python="$PWD/.build/voice-env/bin/python"
whisper_revision=868e55578ea5f69550c046da22aefe11dc6e04c0

# These dependencies generate assets. The packaged app uses neither Python nor FFmpeg.
uv venv --allow-existing --python 3.11 .build/voice-env
uv pip install --python "$voice_python" torch==2.7.1 transformers==4.53.3 numpy==1.26.4 \
  scipy==1.15.3 cython==3.1.2 piper-tts==1.3.0 setuptools==80.9.0 unidecode==1.4.0 phonemizer==3.6.0
python3 scripts/fetch-models.py

(
  cd .build/claude/monotonic_align
  mkdir -p monotonic_align
  "$voice_python" setup.py build_ext --inplace
)
"$voice_python" - <<'PY'
from pathlib import Path
p = Path('.build/claude/text/cleaners.py')
s = p.read_text()
# Claude's Luxembourgish cleaner is grapheme-based and never uses the English phonemizer.
s = s.replace('backend = EspeakBackend("en-us", preserve_punctuation=True, with_stress=True)', 'backend = None')
p.write_text(s)
PY
"$voice_python" scripts/generate-audio.py

if [[ ! -d .build/whisper/.git ]]; then
  git init .build/whisper
  git -C .build/whisper fetch --depth 1 https://github.com/ggml-org/whisper.cpp.git "$whisper_revision"
  git -C .build/whisper checkout --detach FETCH_HEAD
fi
if [[ $(git -C .build/whisper rev-parse HEAD) != "$whisper_revision" ]]; then
  echo 'La copia de whisper.cpp tiene una revisión distinta.' >&2
  exit 1
fi
cmake -S .build/whisper -B .build/whisper-build -DWHISPER_BUILD_TESTS=OFF \
  -DWHISPER_BUILD_SERVER=OFF -DGGML_METAL=OFF -DCMAKE_BUILD_TYPE=Release
cmake --build .build/whisper-build --target whisper-quantize -j 4
mkdir -p .build/openai-whisper/whisper/assets dist/voices
curl -4 -fsSL --retry 2 --max-time 90 \
  https://raw.githubusercontent.com/openai/whisper/main/whisper/assets/mel_filters.npz \
  -o .build/openai-whisper/whisper/assets/mel_filters.npz
convert_model() {
  local source_dir="$1" lang="$2" output_dir=".build/ggml-$2"
  mkdir -p "$output_dir"
  "$voice_python" .build/whisper/models/convert-h5-to-ggml.py \
    "$source_dir" .build/openai-whisper "$output_dir"
  .build/whisper-build/bin/whisper-quantize "$output_dir/ggml-model.bin" "$output_dir/$lang.bin" q5_1
  cp "$output_dir/$lang.bin" "dist/voices/$lang.bin.part"
  mv -f "dist/voices/$lang.bin.part" "dist/voices/$lang.bin"
}
convert_model .build/lux lb
convert_model .build/da-special da
cp .build/da-special/THIRD_PARTY_NOTICES.md dist/voices/da-NOTICES.md
