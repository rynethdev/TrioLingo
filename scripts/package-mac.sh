#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ $(uname -sm) != 'Darwin arm64' ]]; then
  echo 'Este paquete se prepara en macOS arm64.' >&2
  exit 1
fi
if ! command -v cargo >/dev/null && [[ -x "$HOME/.cargo/bin/cargo" ]]; then
  export PATH="$HOME/.cargo/bin:$PATH"
fi
python3 scripts/build-a1-expansion.py
python3 scripts/build-a2-expansion.py
python3 scripts/build-upper-expansion.py
python3 scripts/build-course.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/audit-course.py
cargo build --release --locked
mkdir -p dist
artifact=$(mktemp dist/.idiomas.XXXXXX)
cp target/release/idiomas "$artifact"
chmod 755 "$artifact"
mv -f "$artifact" dist/idiomas
cat > 'dist/Abrir Idiomas.command' <<'LAUNCH'
#!/bin/bash
cd "$(dirname "$0")" || exit 1
exec ./idiomas --open
LAUNCH
chmod +x 'dist/Abrir Idiomas.command'
