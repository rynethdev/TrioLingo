"""Check structural integrity and report curriculum coverage without inflating it.

Run after scripts/build-course.py. Warnings are editorial work, not published skills.
"""
import collections
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEVELS = ("A1", "A2", "B1", "B2", "C1", "C2")


def audit(course, audio_dir):
    errors = []
    warnings = []
    units = course["units"]
    items = course["items"]
    lessons = [lesson for unit in units for lesson in unit["lessons"]]
    item_ids = {item["id"] for item in items}
    for label, values in (("unidad", [u["id"] for u in units]),
                          ("lección", [l["id"] for l in lessons]),
                          ("tarjeta", [i["id"] for i in items])):
        duplicates = [name for name, count in collections.Counter(values).items() if count > 1]
        if duplicates:
            errors.append(f"ID duplicado de {label}: {duplicates[:5]}")

    def check_audio(source, context):
        if source and source.startswith("/assets/audio/"):
            if not (audio_dir / source.rsplit("/", 1)[-1]).is_file():
                errors.append(f"Audio ausente en {context}: {source}")

    for item in items:
        if not item.get("text") or not item.get("translation"):
            errors.append(f"Tarjeta sin texto o traducción: {item['id']}")
        check_audio(item.get("audio"), item["id"])
    for lesson in lessons:
        if not 12 <= len(lesson["tasks"]) <= 16:
            errors.append(f"{lesson['id']}: {len(lesson['tasks'])} tareas (se esperan 12–16)")
        for ref in lesson["items"]:
            if ref not in item_ids:
                errors.append(f"{lesson['id']}: tarjeta desconocida {ref}")
        for index, task in enumerate(lesson["tasks"]):
            label = f"{lesson['id']} tarea {index + 1}"
            if task["kind"] in ("choice", "reading"):
                try:
                    valid = 0 <= int(task["answer"]) < len(task["choices"])
                except (KeyError, TypeError, ValueError):
                    valid = False
                if not valid:
                    errors.append(f"{label}: opción correcta inválida")
                if len(set(task.get("choices", []))) != len(task.get("choices", [])):
                    errors.append(f"{label}: opciones repetidas")
            if task["kind"] in ("cloze", "dictation", "translation") and not task.get("answer"):
                errors.append(f"{label}: falta respuesta")
            if task["kind"] in ("speaking", "writing") and not task.get("model"):
                errors.append(f"{label}: falta modelo")
            for ref in task.get("items", []):
                if ref not in item_ids:
                    errors.append(f"{label}: tarjeta desconocida {ref}")
            check_audio(task.get("audio"), label)
            check_audio(task.get("model_audio"), label)
            for line in task.get("lines", []):
                check_audio(line.get("audio"), label)

    for lang in ("lb", "da"):
        published = {unit["week"] for unit in units if unit["lang"] == lang}
        drafts = [unit["week"] for unit in units if unit["lang"] == lang and unit.get("editorial_status")]
        missing = set(range(1, 201)) - published
        if any(unit["level"] == "A1" for unit in units if unit["lang"] == lang):
            a1_units = [unit for unit in units if unit["lang"] == lang and unit["level"] == "A1"]
            a1_weeks = {unit["week"] for unit in a1_units}
            if len(a1_units) != 20 or a1_weeks != set(range(1, 21)):
                errors.append(f"{lang}: A1 incompleto o semanas A1 repetidas")
        a2_units = [unit for unit in units if unit["lang"] == lang and unit["level"] == "A2"]
        a2_weeks = {unit["week"] for unit in a2_units}
        if len(a2_units) != 24 or a2_weeks != set(range(21, 45)):
            errors.append(f"{lang}: A2 incompleto o semanas A2 repetidas")
        print(f"{lang}: {len(published)}/200 semanas, "
              f"{sum(l['lang'] == lang for l in lessons)}/1000 lecciones, "
              f"{sum(i['lang'] == lang for i in items)} tarjetas; "
              f"sin contenido: {len(missing)} semanas; borradores sin revisar: {len(drafts)}")
        for level in LEVELS:
            level_units = [u for u in units if u["lang"] == lang and u["level"] == level]
            if level_units:
                prompts = [t["prompt"] for u in level_units for l in u["lessons"] for t in l["tasks"]]
                distinct = len(set(prompts))
                if distinct < len(prompts) * 0.6:
                    warnings.append(f"{lang} {level}: solo {distinct} consignas distintas entre {len(prompts)} tareas")
    return errors, warnings


if __name__ == "__main__":
    course = json.loads((ROOT / "content/course.json").read_text())
    errors, warnings = audit(course, ROOT / "web/audio")
    for message in warnings:
        print("AVISO:", message)
    for message in errors[:30]:
        print("ERROR:", message)
    print(f"Integridad: {len(errors)} errores; revisión editorial: {len(warnings)} avisos")
    raise SystemExit(bool(errors))
