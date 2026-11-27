"""Validate content/enrichment/wNNN.json files without writing anything.

Usage: python3 scripts/check-enrichment.py 46 47 48   (or no args: all files)
Safe to run in parallel: it only reads.
"""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("upper", ROOT / "scripts/build-upper-expansion.py")
upper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upper)

base = {(s["lang"], s["week"]): s for s in json.loads((ROOT / "content/upper-expansion.json").read_text())}
weeks = [int(a) for a in sys.argv[1:]] or sorted(int(p.stem[1:]) for p in (ROOT / "content/enrichment").glob("w*.json"))
failed = 0
for week in weeks:
    if week not in upper.EXPECTED:
        print(f"w{week:03d}: no es una semana B1–C2 a enriquecer"); failed += 1; continue
    for lang in ("lb", "da"):
        try:
            block = upper.load_enrichment(week, lang)
            if block is None:
                raise ValueError("falta el archivo")
            scene = base[(lang, week)]
            old_lines = {l["text"] for l in scene["dialogue"]}
            if any(l["text"] in old_lines for l in block["dialogue2"]["lines"]):
                raise ValueError("dialogue2 copia una línea del diálogo base")
            old_vocab = {e["answer"].casefold() for e in scene["exercises"]}
            if any(v["text"].casefold() in old_vocab for v in block["vocab"]):
                raise ValueError("vocab repite una expresión que ya tiene la escena base")
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            print(f"w{week:03d} {lang}: ERROR {error!r}"); failed += 1
print(f"{len(weeks)} semanas revisadas, {failed} errores")
sys.exit(1 if failed else 0)
