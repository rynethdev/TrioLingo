"""Build content/course.json from the existing scenes and curated A1 material.

Each scene becomes a five-day unit:
  day 1 listen, day 2 vocabulary, day 3 grammar, day 4 speak, day 5 read/write/review.

The A2–C2 units reuse existing dialogues, exercises and bundled audio offline.
Run: python3 scripts/build-course.py
"""
import json
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = {"lb": "luxemburgués", "da": "danés"}
LEVEL_ORDER = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}

# id, text, translation, example, example translation, audio line index (or None)
CURATED = {
    "lb-a1": {
        "items": [
            ("lb-moien", "Moien", "Hola", "Moien! Wat kritt Dir?", "¡Hola! ¿Qué le pongo?", 0),
            ("lb-kaffi", "ee Kaffi", "un café", "Ee Kaffi, wann ech gelift.", "Un café, por favor.", 1),
            ("lb-wann-gelift", "wann ech gelift", "por favor", "Ee Kaffi, wann ech gelift.", "Un café, por favor.", 1),
            ("lb-fir-hei", "fir hei", "para aquí", "Fir hei oder fir matzehuelen?", "¿Para aquí o para llevar?", 2),
            ("lb-matzehuelen", "fir matzehuelen", "para llevar", "Fir matzehuelen, wann ech gelift.", "Para llevar, por favor.", 3),
            ("lb-dat-mecht", "Dat mécht", "son / queda en", "Dat mécht dräi Euro.", "Son tres euros.", 4),
            ("lb-drai-euro", "dräi Euro", "tres euros", "Dat mécht dräi Euro.", "Son tres euros.", 4),
            ("lb-merci", "merci", "gracias", "Hei, merci!", "Aquí tiene, ¡gracias!", 5),
            ("lb-hei", "hei", "aquí / aquí tiene", "Hei, merci!", "Aquí tiene, ¡gracias!", 5),
            ("lb-wat-kritt", "Wat kritt Dir?", "¿Qué le pongo?", "Moien! Wat kritt Dir?", "¡Hola! ¿Qué le pongo?", 0),
        ],
        "grammar": {
            "title": "Pedir con cortesía: wann ech gelift",
            "explain": "Para pedir algo en una tienda o cafetería usa una frase corta y añade wann ech gelift (por favor). También puedes usar Ech hätt gär (querría). El verbo va en segunda posición: Ee Kaffi, wann ech gelift.",
            "examples": [
                ("Ee Kaffi, wann ech gelift.", "Un café, por favor."),
                ("Ech hätt gär en Téi.", "Querría un té."),
                ("Fir matzehuelen, wann ech gelift.", "Para llevar, por favor."),
            ],
            "drills": [
                ("Ee Kaffi, ___ ech gelift.", "wann", "wann ech gelift = por favor."),
                ("Ech ___ gär en Téi.", "hätt", "Ech hätt gär = querría."),
                ("Fir ___, wann ech gelift.", "matzehuelen", "fir matzehuelen = para llevar."),
                ("Dat ___ dräi Euro.", "mécht", "Dat mécht ... = son / queda en ..."),
            ],
            "choice": ("¿Cuál es la forma correcta de pedir un café?", ["Ee Kaffi, wann ech gelift.", "Ee Kaffi, merci.", "Ee Kaffi, hei."], 0, "La fórmula cortés lleva wann ech gelift."),
            "translations": [
                ("Un café, por favor.", "Ee Kaffi, wann ech gelift.|E Kaffi, wann ech gelift.", "Puedes usar ee o e según la variedad; wann ech gelift es la fórmula clave."),
                ("¿Para aquí o para llevar?", "Fir hei oder fir matzehuelen?", "Fir hei = para aquí; fir matzehuelen = para llevar."),
            ],
        },
        "cloze": [
            ("Ee ___, wann ech gelift.", "Kaffi", "Kaffi = café."),
            ("Dat mécht ___ Euro.", "dräi", "dräi = tres."),
            ("Hei, ___!", "merci", "merci = gracias."),
        ],
        "pronunciation": ("La vocal de Kaffi y la de hei", "Escucha la vocal breve de Kaffi y la vocal de hei. No las alargues: en luxemburgués la cantidad vocálica cambia el ritmo de la palabra.", [("Kaffi", "café", 1), ("hei", "aquí", 5), ("dräi", "tres", 4)]),
    },
    "lb-a1-presentarte": {
        "items": [
            ("lb-wie-heeschs", "Wéi heeschs du?", "¿Cómo te llamas?", "Moien! Wéi heeschs du?", "¡Hola! ¿Cómo te llamas?", 0),
            ("lb-ech-heeschen", "Ech heeschen", "me llamo", "Ech heeschen Ana.", "Me llamo Ana.", 1),
            ("lb-et-freet-mech", "Et freet mech", "encantado / encantada", "Ech heeschen Ana. Et freet mech!", "Me llamo Ana. ¡Encantada!", 1),
            ("lb-vu-wou", "Vu wou kënns du?", "¿De dónde vienes?", "Vu wou kënns du?", "¿De dónde vienes?", 2),
            ("lb-ech-kommen-aus", "Ech kommen aus", "vengo de", "Ech kommen aus Chile.", "Vengo de Chile.", 3),
            ("lb-wunnen", "wunnen", "vivir", "Ech wunnen elo hei.", "Ahora vivo aquí.", 3),
            ("lb-elo", "elo", "ahora", "Ech wunnen elo hei.", "Ahora vivo aquí.", 3),
            ("lb-hei-2", "hei", "aquí", "Ech wunnen elo hei.", "Ahora vivo aquí.", 3),
            ("lb-an", "an", "y", "Ech kommen aus Chile an ech wunnen hei.", "Vengo de Chile y vivo aquí.", 3),
            ("lb-moien-2", "Moien", "hola", "Moien! Wéi heeschs du?", "¡Hola! ¿Cómo te llamas?", 0),
        ],
        "grammar": {
            "title": "El presente: sinn, kommen, wunnen",
            "explain": "En presente, el verbo cambia con la persona: ech sinn, du bass, hien/si ass; ech kommen, du kënns; ech wunnen, du wunns. Para presentarte basta con dos verbos: heeschen (llamarse), kommen (venir) y wunnen (vivir).",
            "examples": [
                ("Ech heeschen Ana.", "Me llamo Ana."),
                ("Vu wou kënns du?", "¿De dónde vienes?"),
                ("Ech wunnen elo hei.", "Ahora vivo aquí."),
            ],
            "drills": [
                ("Ech ___ aus Chile.", "kommen", "ech kommen = yo vengo."),
                ("Vu wou ___ du?", "kënns", "du kënns = tú vienes."),
                ("Ech ___ elo hei.", "wunnen", "ech wunnen = yo vivo."),
                ("Ech ___ Ana.", "heeschen", "ech heeschen = me llamo."),
            ],
            "choice": ("¿Cuál es correcta para decir «vivo aquí»?", ["Ech wunnen hei.", "Ech wunnt hei.", "Ech wunnen du hei."], 0, "Con ech se usa wunnen."),
            "translations": [
                ("Me llamo Ana y vengo de Chile.", "Ech heeschen Ana an ech kommen aus Chile.", "an = y; kommen aus = venir de."),
                ("¿Dónde vives ahora?", "Wou wunns du elo?", "Wou = dónde; elo = ahora."),
            ],
        },
        "cloze": [
            ("Ech ___ Ana.", "heeschen", "heeschen = llamarse."),
            ("Ech kommen ___ Chile.", "aus", "kommen aus = venir de."),
            ("Ech wunnen ___ hei.", "elo", "elo = ahora."),
        ],
        "pronunciation": ("La ë y la ch de heeschen", "La ë es una vocal central parecida a una e relajada. En heeschen la ch final suena suave. Repite la palabra entera sin separar las sílabas.", [("heeschen", "llamarse", 1), ("Chile", "Chile", 3), ("hei", "aquí", 3)]),
    },
    "lb-a1-anden": {
        "items": [
            ("lb-gudde-moien", "Gudde Moien", "buenos días", "Gudde Moien. Kann ech Iech hëllefen?", "Buenos días. ¿Puedo ayudarle?", 0),
            ("lb-hellefen", "Kann ech Iech hëllefen?", "¿Puedo ayudarle?", "Kann ech Iech hëllefen?", "¿Puedo ayudarle?", 0),
            ("lb-vun-wie", "Vun wéi engem Gleis", "de qué vía", "Vun wéi engem Gleis fiert den Zuch?", "¿De qué vía sale el tren?", 1),
            ("lb-zuch", "den Zuch", "el tren", "Vun wéi engem Gleis fiert den Zuch?", "¿De qué vía sale el tren?", 1),
            ("lb-gleis", "d'Gleis", "la vía", "E fiert vum Gleis zwee.", "Sale de la vía dos.", 2),
            ("lb-fiert", "fiert", "sale / va", "Den Zuch fiert vum Gleis zwee.", "El tren sale de la vía dos.", 2),
            ("lb-zwee", "zwee", "dos", "E fiert vum Gleis zwee.", "Sale de la vía dos.", 2),
            ("lb-neng-auer", "néng Auer", "las nueve", "Fiert en um néng Auer?", "¿Sale a las nueve?", 3),
            ("lb-um", "um", "a la (hora)", "Fiert en um néng Auer?", "¿Sale a las nueve?", 3),
            ("lb-wie", "wéi", "cómo", "Vun wéi engem Gleis fiert den Zuch?", "¿De qué vía sale el tren?", 1),
        ],
        "grammar": {
            "title": "Preguntar por la vía y la hora",
            "explain": "Para preguntar de qué vía sale algo: Vun wéi engem Gleis fiert ...? Para la hora se usa um + número + Auer: um néng Auer. Fíjate en que la pregunta invierte el orden: fiert den Zuch?",
            "examples": [
                ("Vun wéi engem Gleis fiert den Zuch?", "¿De qué vía sale el tren?"),
                ("E fiert vum Gleis zwee.", "Sale de la vía dos."),
                ("Fiert en um néng Auer?", "¿Sale a las nueve?"),
            ],
            "drills": [
                ("Vun wéi engem ___ fiert den Zuch?", "Gleis", "Gleis = vía."),
                ("E fiert vum Gleis ___.", "zwee", "zwee = dos."),
                ("Fiert en ___ néng Auer?", "um", "um néng Auer = a las nueve."),
                ("Kann ech Iech ___?", "hëllefen", "hëllefen = ayudar."),
            ],
            "choice": ("¿Cómo preguntas «¿De qué vía sale el tren?»", ["Vun wéi engem Gleis fiert den Zuch?", "Wéi vill Gleis fiert den Zuch?", "Wou fiert den Zuch?"], 0, "Vun wéi engem Gleis = de qué vía."),
            "translations": [
                ("¿De qué vía sale el tren?", "Vun wéi engem Gleis fiert den Zuch?", "Fíjate en el orden fiert den Zuch."),
                ("Sale a las nueve.", "En fiert um néng Auer.", "um + hora."),
            ],
        },
        "cloze": [
            ("Den ___ fiert vum Gleis zwee.", "Zuch", "Zuch = tren."),
            ("Fiert en um ___ Auer?", "néng", "néng = nueve."),
            ("Kann ech Iech ___?", "hëllefen", "hëllefen = ayudar."),
        ],
        "pronunciation": ("La ch de Zuch y la g de Gleis", "La ch de Zuch se pronuncia en la garganta, sin apoyar la lengua. La g de Gleis es suave. Alterna las dos palabras para notar la diferencia.", [("Zuch", "tren", 1), ("Gleis", "vía", 1), ("néng", "nueve", 3)]),
    },
    "lb-a1-horarios": {
        "items": [
            ("lb-wat-sicht", "wat sicht Dir?", "¿qué busca?", "Moien, wat sicht Dir?", "Hola, ¿qué busca?", 0),
            ("lb-wou-ass", "Wou ass ...?", "¿Dónde está ...?", "Wou ass d'Mëllech?", "¿Dónde está la leche?", 1),
            ("lb-mellech", "d'Mëllech", "la leche", "Wou ass d'Mëllech?", "¿Dónde está la leche?", 1),
            ("lb-hannen", "hannen", "al fondo / detrás", "Si ass hannen op der lénkser Säit.", "Está al fondo a la izquierda.", 2),
            ("lb-lenkser", "op der lénkser Säit", "a la izquierda", "Si ass hannen op der lénkser Säit.", "Está al fondo a la izquierda.", 2),
            ("lb-um-wie-vill", "Um wéi vill Auer", "¿a qué hora?", "Um wéi vill Auer maacht Dir haut zou?", "¿A qué hora cierran hoy?", 3),
            ("lb-zou", "maacht ... zou", "cierra", "Um wéi vill Auer maacht Dir haut zou?", "¿A qué hora cierran hoy?", 3),
            ("lb-haut", "haut", "hoy", "Um wéi vill Auer maacht Dir haut zou?", "¿A qué hora cierran hoy?", 3),
            ("lb-supermarkt", "Supermarkt", "supermercado", "Am Supermarkt fannen ech d'Mëllech.", "En el supermercado encuentro la leche.", None),
            ("lb-wann-gelift-2", "wann ech gelift", "por favor", "Wou ass d'Mëllech, wann ech gelift?", "¿Dónde está la leche, por favor?", 1),
        ],
        "grammar": {
            "title": "Preguntar dónde y a qué hora",
            "explain": "Wou pregunta por el lugar (¿dónde?). Um wéi vill Auer pregunta por la hora (¿a qué hora?). En las respuestas de lugar aparecen hannen (al fondo), vir (delante) y op der lénkser/réchter Säit (a la izquierda/derecha).",
            "examples": [
                ("Wou ass d'Mëllech?", "¿Dónde está la leche?"),
                ("Si ass hannen op der lénkser Säit.", "Está al fondo a la izquierda."),
                ("Um wéi vill Auer maacht Dir haut zou?", "¿A qué hora cierran hoy?"),
            ],
            "drills": [
                ("___ ass d'Mëllech?", "Wou", "Wou = dónde."),
                ("Um wéi vill Auer ___ Dir zou?", "maacht", "maacht ... zou = cierra."),
                ("Si ass hannen op der ___ Säit.", "lénkser", "lénkser = izquierda."),
                ("Wat ___ Dir?", "sicht", "sicht = busca."),
            ],
            "choice": ("¿Cuál pregunta por la hora de cierre?", ["Um wéi vill Auer maacht Dir zou?", "Wou ass d'Mëllech?", "Wat sicht Dir?"], 0, "Um wéi vill Auer = a qué hora."),
            "translations": [
                ("¿Dónde está la leche?", "Wou ass d'Mëllech?", "Wou = dónde."),
                ("¿A qué hora cierran hoy?", "Um wéi vill Auer maacht Dir haut zou?", "haut = hoy; zou = cerrado."),
            ],
        },
        "cloze": [
            ("D'Mëllech ass hannen op der ___ Säit.", "lénkser", "lénkser = izquierda."),
            ("Wat ___ Dir?", "sicht", "sicht = busca."),
            ("Um wéi vill Auer maacht Dir ___ zou?", "haut", "haut = hoy."),
        ],
        "pronunciation": ("La ë de Mëllech y la ou de Wou", "La ë de Mëllech es central y breve. La ou de Wou es un diptongo. Escucha y repite sin convertir la ë en una e española.", [("Mëllech", "leche", 1), ("Wou", "dónde", 1), ("zou", "cerrado", 3)]),
    },
    "lb-a1-farmacia": {
        "items": [
            ("lb-gudde-moien-2", "Gudde Moien", "buenos días", "Gudde Moien, wat braucht Dir?", "Buenos días, ¿qué necesita?", 0),
            ("lb-wat-braucht", "wat braucht Dir?", "¿qué necesita?", "Gudde Moien, wat braucht Dir?", "Buenos días, ¿qué necesita?", 0),
            ("lb-ech-haett", "Ech hätt gär", "querría", "Ech hätt gär e Plooschter.", "Querría una tirita.", 1),
            ("lb-plooschter", "e Plooschter", "una tirita", "Ech hätt gär e Plooschter, wann ech gelift.", "Querría una tirita, por favor.", 1),
            ("lb-klenge-pak", "e klenge Pak", "un paquete pequeño", "Hei ass e klenge Pak.", "Aquí tiene un paquete pequeño.", 2),
            ("lb-wie-vill-kascht", "Wéi vill kascht ...?", "¿Cuánto cuesta ...?", "Wéi vill kascht de Pak?", "¿Cuánto cuesta el paquete?", 3),
            ("lb-pak", "de Pak", "el paquete", "Wéi vill kascht de Pak?", "¿Cuánto cuesta el paquete?", 3),
            ("lb-apdikt", "d'Apdikt", "la farmacia", "An der Apdikt kafe mir e Plooschter.", "En la farmacia compramos una tirita.", None),
            ("lb-hei-ass", "Hei ass", "aquí está", "Hei ass e klenge Pak.", "Aquí tiene un paquete pequeño.", 2),
            ("lb-wann-gelift-3", "wann ech gelift", "por favor", "Ech hätt gär e Plooschter, wann ech gelift.", "Querría una tirita, por favor.", 1),
        ],
        "grammar": {
            "title": "Pedir con Ech hätt gär y preguntar el precio",
            "explain": "Ech hätt gär es la fórmula cortés para pedir en una tienda o farmacia. Para preguntar el precio usa Wéi vill kascht ...? (¿cuánto cuesta...?). La respuesta puede empezar por Hei ass ... (aquí está...).",
            "examples": [
                ("Ech hätt gär e Plooschter, wann ech gelift.", "Querría una tirita, por favor."),
                ("Hei ass e klenge Pak.", "Aquí tiene un paquete pequeño."),
                ("Wéi vill kascht de Pak?", "¿Cuánto cuesta el paquete?"),
            ],
            "drills": [
                ("Ech ___ gär e Plooschter.", "hätt", "Ech hätt gär = querría."),
                ("Wéi vill ___ de Pak?", "kascht", "kascht = cuesta."),
                ("Hei ___ e klenge Pak.", "ass", "Hei ass = aquí está."),
                ("Wat ___ Dir?", "braucht", "braucht = necesita."),
            ],
            "choice": ("¿Cuál es la forma correcta de pedir una tirita?", ["Ech hätt gär e Plooschter, wann ech gelift.", "Ech hunn e Plooschter, merci.", "Wou ass e Plooschter?"], 0, "Ech hätt gär + wann ech gelift."),
            "translations": [
                ("Querría una tirita, por favor.", "Ech hätt gär e Plooschter, wann ech gelift.", "Ech hätt gär = querría."),
                ("¿Cuánto cuesta el paquete?", "Wéi vill kascht de Pak?", "kascht = cuesta."),
            ],
        },
        "cloze": [
            ("Ech hätt gär e ___, wann ech gelift.", "Plooschter", "Plooschter = tirita."),
            ("Wéi vill ___ de Pak?", "kascht", "kascht = cuesta."),
            ("Hei ass e ___ Pak.", "klenge", "klenge = pequeño."),
        ],
        "pronunciation": ("La ch de Plooschter y la k de Pak", "La ch de Plooschter es suave; la k de Pak es clara. Repite las dos palabras y después la frase completa sin acelerar.", [("Plooschter", "tirita", 1), ("Pak", "paquete", 2), ("kascht", "cuesta", 3)]),
    },
    "da-a1": {
        "items": [
            ("da-hej", "Hej", "Hola", "Hej! Hvad skulle det være?", "¡Hola! ¿Qué desea?", 0),
            ("da-kaffe", "en kaffe", "un café", "En kaffe, tak.", "Un café, gracias.", 1),
            ("da-tak", "tak", "gracias", "En kaffe, tak.", "Un café, gracias.", 1),
            ("da-tage-med", "til at tage med", "para llevar", "Til at tage med, tak.", "Para llevar, gracias.", 3),
            ("da-drikke-her", "til at drikke her", "para tomar aquí", "Til at tage med eller til at drikke her?", "¿Para llevar o para tomar aquí?", 2),
            ("da-det-bliver", "Det bliver", "son / queda en", "Det bliver tredive kroner.", "Son treinta coronas.", 4),
            ("da-tredive", "tredive kroner", "treinta coronas", "Det bliver tredive kroner.", "Son treinta coronas.", 4),
            ("da-vaersgo", "Værsgo", "aquí tiene", "Værsgo. Tak!", "Aquí tiene. ¡Gracias!", 5),
            ("da-hvad-skulle", "Hvad skulle det være?", "¿Qué desea?", "Hej! Hvad skulle det være?", "¡Hola! ¿Qué desea?", 0),
            ("da-gerne", "gerne", "con gusto / quiero", "Jeg vil gerne have en kaffe.", "Querría un café.", None),
        ],
        "grammar": {
            "title": "Pedir con Jeg vil gerne have y tak",
            "explain": "La fórmula más útil para pedir es Jeg vil gerne have ... (querría...). Añade tak al final. Para elegir entre aquí o llevar usa til at drikke her / til at tage med.",
            "examples": [
                ("Jeg vil gerne have en kaffe.", "Querría un café."),
                ("Til at tage med, tak.", "Para llevar, gracias."),
                ("Det bliver tredive kroner.", "Son treinta coronas."),
            ],
            "drills": [
                ("Jeg vil gerne ___ en kaffe.", "have", "gerne have = querría."),
                ("En kaffe, ___.", "tak", "tak = gracias."),
                ("Til at ___ med.", "tage", "tage med = llevar."),
                ("Det bliver ___ kroner.", "tredive", "tredive = treinta."),
            ],
            "choice": ("¿Cuál es la forma correcta de pedir un café?", ["Jeg vil gerne have en kaffe, tak.", "Jeg har en kaffe, tak.", "Hvor er en kaffe?"], 0, "Jeg vil gerne have ... tak."),
            "translations": [
                ("Un café, por favor.", "En kaffe, tak.", "tak = gracias / por favor."),
                ("¿Para aquí o para llevar?", "Til at drikke her eller til at tage med?", "drikke her = tomar aquí; tage med = llevar."),
            ],
        },
        "cloze": [
            ("En ___, tak.", "kaffe", "kaffe = café."),
            ("Det bliver ___ kroner.", "tredive", "tredive = treinta."),
            ("Til at tage ___.", "med", "tage med = llevar."),
        ],
        "pronunciation": ("Las vocales de kaffe y la d suave de tredive", "Escucha la vocal breve de kaffe y la d suave de tredive. En danés la d entre vocales no se pronuncia como una d española.", [("kaffe", "café", 1), ("tage", "tomar / llevar", 3), ("tredive", "treinta", 4)]),
    },
    "da-a1-presentarte": {
        "items": [
            ("da-hvad-hedder", "Hvad hedder du?", "¿Cómo te llamas?", "Hej! Hvad hedder du?", "¡Hola! ¿Cómo te llamas?", 0),
            ("da-jeg-hedder", "Jeg hedder", "me llamo", "Jeg hedder Ana.", "Me llamo Ana.", 1),
            ("da-hyggeligt", "Hyggeligt at møde dig", "encantado / encantada", "Jeg hedder Ana. Hyggeligt at møde dig!", "Me llamo Ana. ¡Encantada!", 1),
            ("da-hvor-kommer", "Hvor kommer du fra?", "¿De dónde vienes?", "Hvor kommer du fra?", "¿De dónde vienes?", 2),
            ("da-jeg-kommer-fra", "Jeg kommer fra", "vengo de", "Jeg kommer fra Chile.", "Vengo de Chile.", 3),
            ("da-bor", "bor", "vivo", "Jeg bor her nu.", "Ahora vivo aquí.", 3),
            ("da-nu", "nu", "ahora", "Jeg bor her nu.", "Ahora vivo aquí.", 3),
            ("da-her", "her", "aquí", "Jeg bor her nu.", "Ahora vivo aquí.", 3),
            ("da-og", "og", "y", "Jeg kommer fra Chile og bor her nu.", "Vengo de Chile y ahora vivo aquí.", 3),
            ("da-hej-2", "Hej", "hola", "Hej! Hvad hedder du?", "¡Hola! ¿Cómo te llamas?", 0),
        ],
        "grammar": {
            "title": "El presente: hedder, kommer, bor",
            "explain": "En danés el verbo casi no cambia con la persona: jeg hedder, du hedder; jeg kommer, du kommer; jeg bor, du bor. Para presentarte usa Jeg hedder ... y Jeg kommer fra ...",
            "examples": [
                ("Jeg hedder Ana.", "Me llamo Ana."),
                ("Hvor kommer du fra?", "¿De dónde vienes?"),
                ("Jeg bor her nu.", "Ahora vivo aquí."),
            ],
            "drills": [
                ("Jeg ___ fra Chile.", "kommer", "kommer fra = venir de."),
                ("Jeg ___ her nu.", "bor", "bor = vivir."),
                ("Hvor ___ du fra?", "kommer", "Hvor kommer du fra? = ¿de dónde vienes?"),
                ("Jeg ___ Ana.", "hedder", "hedder = llamarse."),
            ],
            "choice": ("¿Cuál es correcta para decir «vivo aquí»?", ["Jeg bor her.", "Jeg bo her.", "Jeg bor du her."], 0, "Con jeg se usa bor."),
            "translations": [
                ("Me llamo Ana y vengo de Chile.", "Jeg hedder Ana, og jeg kommer fra Chile.", "og = y."),
                ("¿Dónde vives ahora?", "Hvor bor du nu?", "Hvor = dónde; nu = ahora."),
            ],
        },
        "cloze": [
            ("Jeg ___ Ana.", "hedder", "hedder = llamarse."),
            ("Jeg kommer ___ Chile.", "fra", "kommer fra = venir de."),
            ("Jeg bor her ___.", "nu", "nu = ahora."),
        ],
        "pronunciation": ("La ø de møde y la y de hyggeligt", "La ø se hace con labios redondeados y lengua hacia el frente. La y es aún más cerrada. Escucha y repite las palabras sin sustituirlas por una u.", [("hedder", "me llamo", 1), ("møde", "encontrar", 1), ("hyggeligt", "agradable", 1)]),
    },
    "da-a1-anden": {
        "items": [
            ("da-godmorgen", "Godmorgen", "buenos días", "Godmorgen. Kan jeg hjælpe dig?", "Buenos días. ¿Puedo ayudarte?", 0),
            ("da-kan-jeg-hjaelpe", "Kan jeg hjælpe dig?", "¿Puedo ayudarte?", "Godmorgen. Kan jeg hjælpe dig?", "Buenos días. ¿Puedo ayudarte?", 0),
            ("da-hvilket-spor", "Hvilket spor", "qué vía", "Hvilket spor kører toget fra?", "¿De qué vía sale el tren?", 1),
            ("da-toget", "toget", "el tren", "Hvilket spor kører toget fra?", "¿De qué vía sale el tren?", 1),
            ("da-korer", "kører", "sale / va", "Toget kører fra spor to.", "El tren sale de la vía dos.", 2),
            ("da-fra", "fra", "de / desde", "Det kører fra spor to.", "Sale de la vía dos.", 2),
            ("da-spor-to", "spor to", "vía dos", "Det kører fra spor to.", "Sale de la vía dos.", 2),
            ("da-klokken-ni", "klokken ni", "las nueve", "Kører det klokken ni?", "¿Sale a las nueve?", 3),
            ("da-korer-det", "Kører det", "¿Sale?", "Kører det klokken ni?", "¿Sale a las nueve?", 3),
            ("da-hjaelpe", "hjælpe", "ayudar", "Kan jeg hjælpe dig?", "¿Puedo ayudarte?", 0),
        ],
        "grammar": {
            "title": "Preguntar por la vía y la hora",
            "explain": "Para preguntar de qué vía sale el tren: Hvilket spor kører toget fra? Para la hora se usa klokken + número: klokken ni. Observa que fra va al final de la pregunta.",
            "examples": [
                ("Hvilket spor kører toget fra?", "¿De qué vía sale el tren?"),
                ("Det kører fra spor to.", "Sale de la vía dos."),
                ("Kører det klokken ni?", "¿Sale a las nueve?"),
            ],
            "drills": [
                ("Hvilket ___ kører toget fra?", "spor", "spor = vía."),
                ("Det kører fra ___ to.", "spor", "spor to = vía dos."),
                ("Kører det ___ ni?", "klokken", "klokken ni = a las nueve."),
                ("Kan jeg ___ dig?", "hjælpe", "hjælpe = ayudar."),
            ],
            "choice": ("¿Cómo preguntas «¿De qué vía sale el tren?»", ["Hvilket spor kører toget fra?", "Hvor mange spor kører toget?", "Hvor kører toget?"], 0, "Hvilket spor ... fra?"),
            "translations": [
                ("¿De qué vía sale el tren?", "Hvilket spor kører toget fra?", "fra al final."),
                ("Sale a las nueve.", "Det kører klokken ni.", "klokken + hora."),
            ],
        },
        "cloze": [
            ("Hvilket spor kører ___ fra?", "toget", "toget = el tren."),
            ("Det kører fra ___ to.", "spor", "spor = vía."),
            ("Kører det ___ ni?", "klokken", "klokken = a las."),
        ],
        "pronunciation": ("La ø de kører y la t final de toget", "La ø de kører es redondeada. En toget la t final se suaviza. Repite las dos palabras y luego la pregunta completa.", [("toget", "el tren", 1), ("kører", "sale / va", 1), ("klokken", "el reloj / a las", 3)]),
    },
    "da-a1-horarios": {
        "items": [
            ("da-hvad-leder", "Hvad leder du efter?", "¿Qué buscas?", "Hej, hvad leder du efter?", "Hola, ¿qué buscas?", 0),
            ("da-hvor-star", "Hvor står ...?", "¿Dónde está ...?", "Hvor står mælken?", "¿Dónde está la leche?", 1),
            ("da-maelken", "mælken", "la leche", "Hvor står mælken?", "¿Dónde está la leche?", 1),
            ("da-bagerst", "bagerst", "al fondo", "Den står bagerst til venstre.", "Está al fondo a la izquierda.", 2),
            ("da-til-venstre", "til venstre", "a la izquierda", "Den står bagerst til venstre.", "Está al fondo a la izquierda.", 2),
            ("da-hvad-tid", "Hvad tid", "¿a qué hora?", "Hvad tid lukker I i dag?", "¿A qué hora cierran hoy?", 3),
            ("da-lukker", "lukker", "cierra", "Hvad tid lukker I i dag?", "¿A qué hora cierran hoy?", 3),
            ("da-i-dag", "i dag", "hoy", "Hvad tid lukker I i dag?", "¿A qué hora cierran hoy?", 3),
            ("da-supermarked", "supermarked", "supermercado", "Jeg er i supermarkedet.", "Estoy en el supermercado.", None),
            ("da-hjaelpe-2", "hjælpe", "ayudar", "Kan jeg hjælpe dig?", "¿Puedo ayudarte?", None),
        ],
        "grammar": {
            "title": "Preguntar dónde y a qué hora",
            "explain": "Hvor pregunta por el lugar (¿dónde?). Hvad tid pregunta por la hora (¿a qué hora?). En las respuestas de lugar aparecen bagerst (al fondo), forrest (delante) y til venstre/højre (a la izquierda/derecha).",
            "examples": [
                ("Hvor står mælken?", "¿Dónde está la leche?"),
                ("Den står bagerst til venstre.", "Está al fondo a la izquierda."),
                ("Hvad tid lukker I i dag?", "¿A qué hora cierran hoy?"),
            ],
            "drills": [
                ("Hvor ___ mælken?", "står", "står = está."),
                ("Hvad tid ___ I i dag?", "lukker", "lukker = cierra."),
                ("Den står bagerst til ___.", "venstre", "til venstre = a la izquierda."),
                ("Hvad ___ du efter?", "leder", "leder efter = busca."),
            ],
            "choice": ("¿Cuál pregunta por la hora de cierre?", ["Hvad tid lukker I i dag?", "Hvor står mælken?", "Hvad leder du efter?"], 0, "Hvad tid = a qué hora."),
            "translations": [
                ("¿Dónde está la leche?", "Hvor står mælken?", "Hvor = dónde."),
                ("¿A qué hora cierran hoy?", "Hvad tid lukker I i dag?", "i dag = hoy."),
            ],
        },
        "cloze": [
            ("Mælken står bagerst til ___.", "venstre", "til venstre = a la izquierda."),
            ("Hvad ___ du efter?", "leder", "leder = busca."),
            ("Hvad tid ___ I i dag?", "lukker", "lukker = cierra."),
        ],
        "pronunciation": ("La æ de mælken y la e final de venstre", "La æ es más abierta que una e. En venstre la e final es muy breve. Escucha y repite sin añadir una vocal extra al final.", [("mælken", "la leche", 1), ("venstre", "izquierda", 2), ("lukker", "cierra", 3)]),
    },
    "da-a1-farmacia": {
        "items": [
            ("da-godmorgen-2", "Godmorgen", "buenos días", "Godmorgen, hvad har du brug for?", "Buenos días, ¿qué necesitas?", 0),
            ("da-hvad-brug", "hvad har du brug for?", "¿qué necesitas?", "Godmorgen, hvad har du brug for?", "Buenos días, ¿qué necesitas?", 0),
            ("da-jeg-vil-gerne", "Jeg vil gerne have", "querría", "Jeg vil gerne have nogle plastre.", "Querría tiritas.", 1),
            ("da-plastre", "plastre", "tiritas", "Jeg vil gerne have nogle plastre, tak.", "Querría tiritas, por favor.", 1),
            ("da-lille-pakke", "en lille pakke", "un paquete pequeño", "Her er en lille pakke.", "Aquí tiene un paquete pequeño.", 2),
            ("da-hvad-koster", "Hvad koster ...?", "¿Cuánto cuesta ...?", "Hvad koster pakken?", "¿Cuánto cuesta el paquete?", 3),
            ("da-pakken", "pakken", "el paquete", "Hvad koster pakken?", "¿Cuánto cuesta el paquete?", 3),
            ("da-apoteket", "apoteket", "la farmacia", "Jeg køber plastre på apoteket.", "Compro tiritas en la farmacia.", None),
            ("da-her-er", "Her er", "aquí está", "Her er en lille pakke.", "Aquí tiene un paquete pequeño.", 2),
            ("da-mange-tak", "mange tak", "muchas gracias", "Mange tak for hjælpen.", "Muchas gracias por la ayuda.", None),
        ],
        "grammar": {
            "title": "Pedir con Jeg vil gerne have y preguntar el precio",
            "explain": "Jeg vil gerne have ... es la fórmula cortés para pedir. Para preguntar el precio usa Hvad koster ...? (¿cuánto cuesta...?). La respuesta puede empezar por Her er ... (aquí está...).",
            "examples": [
                ("Jeg vil gerne have nogle plastre, tak.", "Querría tiritas, por favor."),
                ("Her er en lille pakke.", "Aquí tiene un paquete pequeño."),
                ("Hvad koster pakken?", "¿Cuánto cuesta el paquete?"),
            ],
            "drills": [
                ("Jeg vil gerne ___ nogle plastre.", "have", "gerne have = querría."),
                ("Hvad ___ pakken?", "koster", "koster = cuesta."),
                ("Her er en lille ___.", "pakke", "pakke = paquete."),
                ("Hvad har du ___ for?", "brug", "brug for = necesitar."),
            ],
            "choice": ("¿Cuál es la forma correcta de pedir tiritas?", ["Jeg vil gerne have nogle plastre, tak.", "Jeg har nogle plastre, tak.", "Hvor er nogle plastre?"], 0, "Jeg vil gerne have ... tak."),
            "translations": [
                ("Querría tiritas, por favor.", "Jeg vil gerne have nogle plastre, tak.", "nogle = algunas."),
                ("¿Cuánto cuesta el paquete?", "Hvad koster pakken?", "koster = cuesta."),
            ],
        },
        "cloze": [
            ("Jeg vil gerne have nogle ___, tak.", "plastre", "plastre = tiritas."),
            ("Hvad ___ pakken?", "koster", "koster = cuesta."),
            ("Her er en lille ___.", "pakke", "pakke = paquete."),
        ],
        "pronunciation": ("La a de plastre y la e final de pakke", "La a de plastre es breve; la e final de pakke casi no se pronuncia. Repite las dos palabras y después la frase completa.", [("plastre", "tiritas", 1), ("pakke", "paquete", 2), ("koster", "cuesta", 3)]),
    },
}


def audio(sid, kind, index):
    return f"/assets/audio/{sid}-{kind}-{index}.mp3"


def course_title(title):
    return title.replace("Control ", "Práctica guiada ", 1) if title.startswith("Control ") else title


def task(kind, prompt, **kw):
    value = {"kind": kind, "prompt": prompt}
    value.update(kw)
    return value


def choice(prompt, correct, distractors, explain, seed):
    options = [correct] + [d for d in distractors if d != correct]
    # Keep exactly three options.
    options = options[:3]
    random.Random(seed).shuffle(options)
    return task("choice", prompt, choices=options, answer=str(options.index(correct)), explain=explain)


def sample(pool, count, seed):
    unique = []
    for value in pool:
        if value not in unique:
            unique.append(value)
    random.Random(seed).shuffle(unique)
    return unique[:count]


def vocab_choice(item, items, mode, seed):
    if mode == "to_es":
        correct = item["translation"]
        pool = [other["translation"] for other in items if other["id"] != item["id"]]
        prompt = f"¿Qué significa «{item['text']}»?"
        explain = f"{item['text']} = {item['translation']}."
    else:
        correct = item["text"]
        pool = [other["text"] for other in items if other["id"] != item["id"]]
        prompt = f"¿Cómo se dice «{item['translation']}»?"
        explain = f"{item['translation']} = {item['text']}."
    return choice(prompt, correct, sample(pool, 2, seed), explain, seed)


def item_cloze(item):
    example = item["example"]
    if item["text"] not in example:
        return None
    return task("cloze", example.replace(item["text"], "___", 1), answer=item["text"],
                explain=f"{item['text']} = {item['translation']}.")


def item_translation(item, lang, seed):
    return task("translation", f"Traduce al {LANGS[lang]}: «{item['translation']}»",
                answer=item["text"], explain=f"{item['text']} = {item['translation']}.")


ROADMAP = [
        {"level": "A1", "start": 1, "end": 20, "hours": 100, "title": "Supervivencia",
         "focus": "Presentarte, comprar, orientarte, pedir ayuda y hablar de tu día."},
        {"level": "A2", "start": 21, "end": 44, "hours": 220, "title": "Vida cotidiana",
         "focus": "Vivienda, salud, trabajo, trámites y relaciones sociales."},
        {"level": "B1", "start": 45, "end": 80, "hours": 400, "title": "Independencia",
         "focus": "Narrar, opinar, resolver problemas y empezar el track profesional."},
        {"level": "B2", "start": 81, "end": 116, "hours": 580, "title": "Trabajo real",
         "focus": "Reuniones, correos, presentaciones, negociación y sector."},
        {"level": "C1", "start": 117, "end": 158, "hours": 790, "title": "Precisión",
         "focus": "Matices, registro, argumentación, informes y mediación."},
        {"level": "C2", "start": 159, "end": 200, "hours": 1000, "title": "Maestría",
         "focus": "Estilo, ironía, textos complejos y capstone profesional."},
    ]


def extract_spanish(prompt):
    match = re.search(r"«([^»]+)»", prompt or "")
    return match.group(1) if match else ""


def line_cloze(line):
    words = re.findall(r"[^\W\d_]+", line["text"], flags=re.UNICODE)
    candidates = [word for word in words if len(word) >= 4]
    if not candidates:
        return None
    target = max(candidates, key=len)
    prompt = re.sub(r"(?<!\w)" + re.escape(target) + r"(?!\w)", "___", line["text"], count=1)
    if prompt == line["text"]:
        return None
    return task("cloze", prompt, answer=target, explain=line["es"])


def generic_items(scene):
    sid = scene["id"]
    lang = scene["lang"]
    level = scene["level"]
    items = []
    seen = set()

    def add(text, translation, example, example_es, source):
        text = (text or "").strip()
        translation = (translation or "").strip()
        if not text or not translation:
            return
        key = text.casefold()
        if key in seen:
            return
        seen.add(key)
        items.append({
            "id": f"{sid}-i{len(items)}",
            "lang": lang,
            "level": level,
            "text": text,
            "translation": translation,
            "example": example or text,
            "example_es": example_es or translation,
            "kind": "chunk" if " " in text else "word",
            "audio": source,
            "tags": [scene["title"]],
        })

    for index, line_data in enumerate(scene.get("dialogue", [])):
        add(line_data["text"], line_data["es"], line_data["text"], line_data["es"],
            audio(sid, "line", index))
    for index, turn in enumerate(scene.get("turns", [])):
        add(turn["model"], turn.get("model_es", ""), turn["model"], turn.get("model_es", ""),
            audio(sid, "model", index))
    for exercise in scene.get("exercises", []):
        if exercise.get("kind") != "vocabulary":
            continue
        answer = (exercise.get("answer") or "").strip()
        translation = extract_spanish(exercise.get("prompt", ""))
        example = answer
        example_es = translation
        source = None
        for index, line_data in enumerate(scene.get("dialogue", [])):
            if answer and answer.casefold() in line_data["text"].casefold():
                example = line_data["text"]
                example_es = line_data["es"]
                source = audio(sid, "line", index)
                break
        add(answer, translation, example, example_es, source)
    enrichment = scene.get("enrichment") or {}
    for entry in enrichment.get("vocab", []):
        source = None
        for index, line_data in enumerate(enrichment.get("dialogue", [])):
            if entry["example"] == line_data["text"]:
                source = audio(sid, "line2", index)
                break
        add(entry["text"], entry["es"], entry["example"], entry["example_es"], source)
    return items


def build_generic_unit(scene, week, items, checkpoint):
    sid = scene["id"]
    lang = scene["lang"]
    level = scene["level"]
    dialogue = scene["dialogue"]
    turns = scene.get("turns", [])
    exercises = scene.get("exercises", [])
    grammar = [exercise for exercise in exercises if exercise.get("kind") == "grammar"]
    listening = scene["listening"]
    extra = scene.get("enrichment")
    # Lines available to padding: the base dialogue plus, when authored, the
    # second conversation, so filler tasks stop recycling the same four lines.
    line_pool = [(line_data, audio(sid, "line", index), f"la frase {index + 1} del diálogo")
                 for index, line_data in enumerate(dialogue)]
    if extra:
        line_pool += [(line_data, audio(sid, "line2", index),
                       f"la frase {index + 1} de la segunda conversación")
                      for index, line_data in enumerate(extra["dialogue"])]

    def vc(item, mode, suffix):
        return vocab_choice(item, items, mode, f"{sid}-{suffix}")

    def tr(item, suffix):
        return item_translation(item, lang, f"{sid}-{suffix}")

    def review(ids=None):
        chosen = ids if ids else [item["id"] for item in items]
        return task("review", "Estas expresiones entran hoy en tu repaso.", items=chosen)

    built = []  # tasks of earlier lessons in this unit (pad runs once per lesson)

    def pad(tasks, day, target=12):
        prompts = {task_item["prompt"] for task_item in tasks}
        # Enriched weeks have enough material: never let filler ask the same
        # question (prompt + answer) a third time across the unit.
        used = {}
        for task_item in built + tasks:
            key = (task_item["prompt"], str(task_item.get("answer")))
            used[key] = used.get(key, 0) + 1
        index = 0
        while len(tasks) < target and items and index < len(items) * 8:
            item = items[index % len(items)]
            if scene.get("editorial_status"):
                line_data, line_audio, line_label = line_pool[(index + day) % len(line_pool)]
                mode = index % 5
                if mode == 0:
                    candidate = task("dictation", f"Escucha y escribe {line_label}.",
                                     answer=line_data["text"], audio=line_audio,
                                     explain=line_data["es"])
                elif mode == 1:
                    candidate = line_cloze(line_data)
                elif mode == 2:
                    candidate = task("translation", f"Traduce sin mirar al {LANGS[lang]}: «{line_data['es']}»",
                                     answer=line_data["text"], explain="Compara con el diálogo después de responder.")
                elif mode == 3:
                    candidate = task("writing", f"Escribe otra frase útil en esta situación usando «{item['translation']}».",
                                     model=item["text"], rubric="Una frase comprensible y adecuada a la situación.")
                else:
                    candidate = vc(item, "to_es", f"g{day}-p{index}")
                if candidate is None:
                    index += 1
                    continue
            else:
                candidate = vc(item, "to_es" if index % 2 == 0 else "from_es", f"g{day}-p{index}")
            key = (candidate["prompt"], str(candidate.get("answer")))
            if extra and used.get(key, 0) >= 2:
                index += 1
                continue
            if candidate["prompt"] not in prompts:
                tasks.append(candidate)
                prompts.add(candidate["prompt"])
                used[key] = used.get(key, 0) + 1
            elif not scene.get("editorial_status"):
                candidate = tr(item, f"g{day}-pt{index}")
                if candidate["prompt"] not in prompts:
                    tasks.append(candidate)
                    prompts.add(candidate["prompt"])
            index += 1
        built.extend(tasks)

    def speaking_turn(turn, index):
        return task("speaking", turn["prompt"], es=turn.get("es", ""),
                    model=turn["model"], accepted=turn.get("accepted") or [turn["model"]],
                    tip=turn.get("tip", ""), audio=audio(sid, "prompt", index),
                    model_audio=audio(sid, "model", index),
                    items=[items[index % len(items)]["id"]])

    def dialogue_lines():
        return [{"speaker": line_data["speaker"], "text": line_data["text"], "es": line_data["es"],
                 "audio": audio(sid, "line", index)}
                for index, line_data in enumerate(dialogue)]

    def ids(start, end):
        return [item["id"] for item in items[start:end]]

    # Day 1: listen and notice.
    tasks = [
        task("dialogue", "Escucha el diálogo y sigue el texto.", lines=dialogue_lines(),
             explain="Puedes repetir cada línea antes de responder."),
        task("choice", listening["prompt"], choices=listening["choices"],
             answer=str(listening["answer"]),
             explain="Vuelve a escuchar el diálogo completo antes de elegir."),
        task("dictation", "Escucha y escribe la primera frase.", answer=dialogue[0]["text"],
             audio=audio(sid, "line", 0), explain=dialogue[0]["es"]),
        tr(items[0], "g1-t0"),
        vc(items[1], "to_es", "g1-v1"),
        vc(items[2], "from_es", "g1-v2"),
    ]
    if turns:
        tasks.append(speaking_turn(turns[0], 0))
    pad(tasks, 1)
    tasks.append(review(ids(0, 3)))
    lessons = [{
        "id": f"{sid}-d1", "lang": lang, "level": level, "week": week, "day": 1,
        "unit": sid, "title": "Escuchar y entender",
        "goal": "Entender la situación y reconocer las frases clave.",
        "tasks": tasks, "items": ids(0, 3),
    }]

    # Day 2: vocabulary in context.
    tasks = []
    for index, item in enumerate(items[:4]):
        tasks.append(vc(item, "to_es" if index % 2 == 0 else "from_es", f"g2-v{index}"))
    for index, exercise in enumerate(grammar):
        tasks.append(task("cloze", exercise["prompt"], answer=exercise["answer"],
                          explain=exercise.get("explanation", "")))
    if not grammar:
        cloze = line_cloze(dialogue[1] if len(dialogue) > 1 else dialogue[0])
        if cloze:
            tasks.append(cloze)
    for index, item in enumerate(items[:2]):
        tasks.append(tr(item, f"g2-t{index}"))
    pron = [item for item in items if item.get("audio")][:3]
    if pron:
        tasks.append(task("pronunciation", "Escucha y repite estas expresiones.",
                          tip="Imita el ritmo y la entonación; después repite sin mirar.",
                          lines=[{"text": item["text"], "es": item["translation"], "audio": item["audio"]}
                                 for item in pron]))
    if extra:
        # New expressions, each in its own example sentence (not the dialogue).
        for entry in extra["vocab"]:
            text, example = entry["text"].strip(), entry["example"]
            at = example.casefold().find(text.casefold())
            if at >= 0:
                tasks.append(task("cloze", example[:at] + "___" + example[at + len(text):],
                                  answer=example[at:at + len(text)],
                                  explain=f"{example} = {entry['example_es']}"))
    pad(tasks, 2)
    tasks.append(review(ids(3, 7)))
    lessons.append({
        "id": f"{sid}-d2", "lang": lang, "level": level, "week": week, "day": 2,
        "unit": sid, "title": "Vocabulario en contexto",
        "goal": "Fijar las palabras y expresiones de la situación.",
        "tasks": tasks, "items": ids(3, 7),
    })

    # Day 3: structure drills from the scene; not a full grammar syllabus.
    tasks = []
    for exercise in grammar:
        tasks.append(task("cloze", exercise["prompt"], answer=exercise["answer"],
                          explain=exercise.get("explanation", "")))
    for offset in range(2):
        cloze = line_cloze(dialogue[(offset + 1) % len(dialogue)])
        if cloze:
            tasks.append(cloze)
    tasks.append(tr(items[1], "g3-t1"))
    for index in range(2, 6):
        tasks.append(vc(items[index % len(items)], "to_es" if index % 2 == 0 else "from_es", f"g3-v{index}"))
    if extra:
        focus = extra["grammar"]
        for entry in focus["items"]:
            tasks.append(task("cloze", entry["prompt"], answer=entry["answer"],
                              explain=f"{focus['focus']}. {focus['explain']} — {entry['es']}"))
    pad(tasks, 3)
    tasks.append(review(ids(7, 9)))
    lessons.append({
        "id": f"{sid}-d3", "lang": lang, "level": level, "week": week, "day": 3,
        "unit": sid, "title": "Estructuras en contexto",
        "goal": "Practicar formas y frases de la escena.",
        "tasks": tasks, "items": ids(7, 9),
    })

    # Day 4: speak.
    tasks = []
    for index, turn in enumerate(turns[:2]):
        tasks.append(speaking_turn(turn, index))
    if scene.get("editorial_status"):
        tasks.append(task("writing", "Escribe qué responderías al interlocutor en esta situación.",
                          model=dialogue[-1]["text"],
                          rubric="Responde a la situación con cortesía y una frase completa."))
    else:
        tasks.append(task("writing", scene["writing"]["prompt"], model=scene["writing"]["model"],
                          rubric=scene["writing"]["rubric"]))
    tasks.append(task("dictation", "Escucha y escribe una frase del diálogo.",
                      answer=dialogue[1]["text"], audio=audio(sid, "line", 1),
                      explain=dialogue[1]["es"]))
    cloze = line_cloze(dialogue[-1])
    if cloze:
        tasks.append(cloze)
    for index in range(3):
        tasks.append(vc(items[(index + 3) % len(items)], "to_es" if index % 2 == 0 else "from_es", f"g4-v{index}"))
    if extra:
        second = extra["dialogue"]
        tasks.append(task("dialogue", f"Escucha otra conversación. {extra['context']}",
                          lines=[{"speaker": l["speaker"], "text": l["text"], "es": l["es"],
                                  "audio": audio(sid, "line2", i)} for i, l in enumerate(second)],
                          explain="Escucha primero sin leer la traducción."))
        tasks.append(task("choice", extra["listening"]["prompt"], choices=extra["listening"]["choices"],
                          answer=str(extra["listening"]["answer"]),
                          explain="La respuesta no está en una sola frase: piensa en toda la conversación."))
        ask, reply = len(second) // 2 - 1, len(second) // 2
        tasks.append(task("speaking", second[ask]["text"], es=f"Responde: {second[reply]['es']}",
                          model=second[reply]["text"], accepted=[second[reply]["text"]],
                          tip="Responde como en la segunda conversación; después compara con el modelo.",
                          audio=audio(sid, "line2", ask), model_audio=audio(sid, "line2", reply),
                          items=[items[-1]["id"]]))
    pad(tasks, 4)
    tasks.append(review(ids(9, 12)))
    lessons.append({
        "id": f"{sid}-d4", "lang": lang, "level": level, "week": week, "day": 4,
        "unit": sid, "title": "Hablar sin miedo",
        "goal": "Responder con tus propias palabras en la situación.",
        "tasks": tasks, "items": ids(9, 12),
    })

    # Day 5: read, write, close.
    tasks = [
        task("reading", scene["reading"]["prompt"], text=scene["reading"]["text"],
             choices=scene["reading"]["choices"], answer=str(scene["reading"]["answer"]),
             audio=audio(sid, "reading", 0) if scene.get("editorial_status") else None,
             explain="Vuelve al texto y busca la información exacta."),
        task("writing", scene["writing"]["prompt"], model=scene["writing"]["model"],
             rubric=scene["writing"]["rubric"]),
        task("dictation", "Escucha y escribe la última frase del diálogo.",
             answer=dialogue[-1]["text"], audio=audio(sid, "line", len(dialogue) - 1),
             explain=dialogue[-1]["es"]),
        tr(items[-1], "g5-t0"),
    ]
    for index in range(3):
        tasks.append(vc(items[index % len(items)], "from_es" if index % 2 == 0 else "to_es", f"g5-v{index}"))
    if checkpoint:
        tasks.insert(0, task("choice", f"Repaso guiado {level}: {listening['prompt']}",
                             choices=listening["choices"], answer=str(listening["answer"]),
                             explain="Control de nivel: vuelve al diálogo si dudas."))
    if extra:
        tasks.append(task("writing", extra["transfer"]["prompt"], model=extra["transfer"]["model"],
                          rubric=extra["transfer"]["rubric"]))
    pad(tasks, 5)
    tasks.append(review())
    lessons.append({
        "id": f"{sid}-d5", "lang": lang, "level": level, "week": week, "day": 5,
        "unit": sid,
        "title": f"Repaso final {level}" if checkpoint else "Leer, escribir y cerrar",
        "goal": "Leer, escribir y cerrar el bloque con una tarea completa.",
        "tasks": tasks, "items": [], "checkpoint": checkpoint,
    })

    return {
        "id": sid, "lang": lang, "level": level, "week": week,
        "title": course_title(scene["title"]), "can_do": scene["goal"], "scene": sid,
        "editorial_status": scene.get("editorial_status"),
        "lessons": lessons,
    }


def build_course():
    scenes = []
    for name in ("scenes.json", "itinerary.json", "a1-expansion.json", "a2-expansion.json", "upper-expansion.json"):
        scenes.extend(json.loads((ROOT / "content" / name).read_text()))
    scenes = [scene for scene in scenes if scene["lang"] in LANGS]
    scenes.sort(key=lambda scene: (scene["lang"], LEVEL_ORDER.get(scene.get("level"), 99), scene.get("week", 1), scene["id"]))
    a1_scenes = [scene for scene in scenes if scene.get("level") == "A1" and scene["id"] in CURATED]
    generic_scenes = [scene for scene in scenes if scene["id"] not in CURATED]

    course_items = []
    units = []
    for scene in a1_scenes:
        sid = scene["id"]
        lang = scene["lang"]
        data = CURATED[sid]
        items = []
        for index, (item_id, text, translation, example, example_es, line) in enumerate(data["items"]):
            item = {
                "id": item_id,
                "lang": lang,
                "level": "A1",
                "text": text,
                "translation": translation,
                "example": example,
                "example_es": example_es,
                "kind": "chunk" if " " in text else "word",
                "audio": audio(sid, "line", line) if line is not None else None,
                "tags": [scene["title"]],
            }
            items.append(item)
            course_items.append(item)

        grammar = data["grammar"]
        pronunciation = data["pronunciation"]
        week = scene.get("week", 1)
        lessons = []

        # Day 1: listen and notice.
        tasks = [
            task("dialogue", "Escucha el diálogo y sigue el texto.", lines=[
                {"speaker": line["speaker"], "text": line["text"], "es": line["es"],
                 "audio": audio(sid, "line", index)}
                for index, line in enumerate(scene["dialogue"])
            ], explain="Puedes volver a cada línea tantas veces como necesites."),
            task("choice", scene["listening"]["prompt"], choices=scene["listening"]["choices"],
                 answer=str(scene["listening"]["answer"]),
                 lines=[{"speaker": line["speaker"], "text": line["text"], "es": line["es"],
                         "audio": audio(sid, "line", index)}
                        for index, line in enumerate(scene["dialogue"])],
                 explain="Vuelve a escuchar el diálogo completo antes de elegir."),
            task("dictation", "Escucha y escribe la frase.", answer=scene["dialogue"][1]["text"],
                 audio=audio(sid, "line", 1), explain=scene["dialogue"][1]["es"]),
            task("translation", f"Traduce al {LANGS[lang]}: «{scene['dialogue'][0]['es']}»",
                 answer=scene["dialogue"][0]["text"], explain="Compara con el modelo del diálogo."),
            task("cloze", data["cloze"][0][0], answer=data["cloze"][0][1], explain=data["cloze"][0][2]),
            task("speaking", scene["turns"][0]["prompt"], es=scene["turns"][0]["es"],
                 model=scene["turns"][0]["model"], accepted=scene["turns"][0]["accepted"] or [scene["turns"][0]["model"]],
                 tip=scene["turns"][0]["tip"], audio=audio(sid, "prompt", 0), model_audio=audio(sid, "model", 0),
                 items=[items[0]["id"]]),
            task("pronunciation", "Escucha y repite. Marca cómo te salió.", tip=pronunciation[1],
                 lines=[{"text": word, "es": es, "audio": audio(sid, "line", line)}
                        for word, es, line in pronunciation[2]]),
            vocab_choice(items[0], items, "to_es", sid + "-v1"),
            vocab_choice(items[1], items, "from_es", sid + "-v2"),
            vocab_choice(items[2], items, "to_es", sid + "-v3"),
            vocab_choice(items[3], items, "from_es", sid + "-v4"),
            vocab_choice(items[4], items, "to_es", sid + "-v5"),
        ]
        if len(data["cloze"]) > 1:
            tasks.append(task("cloze", data["cloze"][1][0], answer=data["cloze"][1][1], explain=data["cloze"][1][2]))
        if len(scene["turns"]) > 1:
            tasks.append(task("speaking", scene["turns"][1]["prompt"], es=scene["turns"][1]["es"],
                              model=scene["turns"][1]["model"],
                              accepted=scene["turns"][1]["accepted"] or [scene["turns"][1]["model"]],
                              tip=scene["turns"][1]["tip"], audio=audio(sid, "prompt", 1),
                              model_audio=audio(sid, "model", 1), items=[items[1]["id"]]))
        tasks.append(task("review", "Estas palabras entran hoy en tu repaso.", items=[items[0]["id"], items[1]["id"], items[2]["id"]]))
        lessons.append({
            "id": f"{sid}-d1", "lang": lang, "level": "A1", "week": week, "day": 1,
            "unit": sid, "title": "Escuchar y entender", "goal": scene["goal"],
            "tasks": tasks, "items": [items[0]["id"], items[1]["id"], items[2]["id"]],
        })

        # Day 2: vocabulary.
        tasks = []
        for offset, item in enumerate(items[3:7]):
            tasks.append(vocab_choice(item, items, "to_es" if offset % 2 == 0 else "from_es", sid + f"-d2-{offset}"))
        for item in items[3:5]:
            cloze = item_cloze(item)
            if cloze:
                tasks.append(cloze)
        audio_item = next((item for item in items if item["audio"]), None)
        if audio_item:
            tasks.append(choice("Escucha y elige la palabra que oyes.", audio_item["text"],
                                sample([item["text"] for item in items if item["id"] != audio_item["id"]], 2, sid + "-audio"),
                                f"Has oído «{audio_item['text']}».", sid + "-audio-choice",))
            tasks[-1]["audio"] = audio_item["audio"]
        tasks.append(task("speaking", "Di estas tres palabras en voz alta: " + ", ".join(item["text"] for item in items[3:6]),
                          model=items[3]["text"], accepted=[items[3]["text"]], tip="Grábate y compara con el audio del diálogo.",
                          items=[item["id"] for item in items[3:6]]))
        tasks.append(task("writing", "Escribe dos frases con dos palabras de la lista.",
                          model=items[3]["example"] + " " + items[4]["example"],
                          rubric="Usa al menos dos palabras nuevas y una estructura completa.",
                          items=[items[3]["id"], items[4]["id"]]))
        for item in items[5:7]:
            cloze = item_cloze(item)
            if cloze:
                tasks.append(cloze)
        for index, item in enumerate(items[5:7]):
            tasks.append(item_translation(item, lang, sid + f"-d2-t{index}"))
        tasks.append(vocab_choice(items[7], items, "to_es", sid + "-d2-7"))
        tasks.append(task("pronunciation", "Escucha estas palabras y repítelas.", tip=pronunciation[1],
                          lines=[{"text": word, "es": es, "audio": audio(sid, "line", line)}
                                 for word, es, line in pronunciation[2]]))
        tasks.append(task("review", "Marca las palabras que ya reconoces sin mirar.", items=[item["id"] for item in items[3:8]]))
        lessons.append({
            "id": f"{sid}-d2", "lang": lang, "level": "A1", "week": week, "day": 2,
            "unit": sid, "title": "Vocabulario en contexto", "goal": "Fijar las palabras clave de la situación.",
            "tasks": tasks, "items": [item["id"] for item in items[3:7]],
        })

        # Day 3: grammar.
        tasks = [task("grammar", grammar["title"], text=grammar["explain"],
                      lines=[{"text": text, "es": es, "audio": None} for text, es in grammar["examples"]])]
        for prompt, answer, explain in grammar["drills"]:
            tasks.append(task("cloze", prompt, answer=answer, explain=explain))
        prompt, options, answer, explain = grammar["choice"]
        tasks.append(choice(prompt, options[answer], [value for index, value in enumerate(options) if index != answer], explain, sid + "-gchoice"))
        for es, answer, explain in grammar["translations"]:
            tasks.append(task("translation", f"Traduce al {LANGS[lang]}: «{es}»", answer=answer, explain=explain))
        tasks.append(task("speaking", "Usa la estructura de hoy en una frase propia.",
                          model=grammar["examples"][0][0], accepted=[grammar["examples"][0][0]],
                          tip="Puedes cambiar el sustantivo o el lugar. Lo importante es usar la estructura.",
                          items=[items[7]["id"]]))
        tasks.append(task("writing", "Escribe una frase con la estructura de hoy.",
                          model=grammar["examples"][0][0],
                          rubric="La frase debe ser completa y usar la estructura explicada.",
                          items=[items[7]["id"]]))
        tasks.append(vocab_choice(items[8], items, "from_es", sid + "-d3-v8"))
        tasks.append(vocab_choice(items[9], items, "to_es", sid + "-d3-v9"))
        line_index = min(4, len(scene["dialogue"]) - 1)
        tasks.append(task("dictation", "Escucha y escribe la frase del diálogo.", answer=scene["dialogue"][line_index]["text"],
                          audio=audio(sid, "line", line_index), explain=scene["dialogue"][line_index]["es"]))
        tasks.append(task("review", "Repasa la gramática con estas palabras de la unidad.", items=[items[7]["id"], items[8]["id"], items[9]["id"]]))
        lessons.append({
            "id": f"{sid}-d3", "lang": lang, "level": "A1", "week": week, "day": 3,
            "unit": sid, "title": "Gramática para usar", "goal": grammar["title"],
            "tasks": tasks, "items": [items[7]["id"], items[8]["id"]],
        })

        # Day 4: speak.
        tasks = []
        for index, turn in enumerate(scene["turns"]):
            tasks.append(task("speaking", turn["prompt"], es=turn["es"], model=turn["model"],
                              accepted=turn["accepted"] or [turn["model"]], tip=turn["tip"],
                              audio=audio(sid, "prompt", index), model_audio=audio(sid, "model", index)))
        tasks.append(task("speaking", f"Roleplay: {scene['setup']} Responde con una frase completa.",
                          model=scene["turns"][-1]["model"], accepted=[scene["turns"][-1]["model"]],
                          tip="No busques la frase perfecta: primero di la idea, luego mejora la forma."))
        tasks.append(task("pronunciation", "Repite el sonido del día y grábate.", tip=pronunciation[1],
                          lines=[{"text": word, "es": es, "audio": audio(sid, "line", line)}
                                 for word, es, line in pronunciation[2]]))
        tasks.append(task("review", "Repasa las palabras de esta unidad en Vocabulario.",
                          items=[item["id"] for item in items]))
        tasks.append(task("choice", scene["listening"]["prompt"], choices=scene["listening"]["choices"],
                          answer=str(scene["listening"]["answer"]),
                          explain="Vuelve a escuchar el diálogo completo antes de elegir."))
        tasks.append(task("cloze", data["cloze"][2][0], answer=data["cloze"][2][1], explain=data["cloze"][2][2]))
        tasks.append(vocab_choice(items[0], items, "from_es", sid + "-d4-v0"))
        tasks.append(vocab_choice(items[6], items, "to_es", sid + "-d4-v6"))
        tasks.append(task("writing", "Escribe la respuesta que darías en esta situación.",
                          model=scene["turns"][0]["model"],
                          rubric="Una frase completa, natural y adecuada al contexto.",
                          items=[items[0]["id"]]))
        line_index = min(3, len(scene["dialogue"]) - 1)
        tasks.append(task("dictation", "Escucha y escribe otra línea del diálogo.", answer=scene["dialogue"][line_index]["text"],
                          audio=audio(sid, "line", line_index), explain=scene["dialogue"][line_index]["es"]))
        tasks.append(task("speaking", "Repite el modelo con la misma entonación.", model=scene["turns"][0]["model"],
                          accepted=[scene["turns"][0]["model"]], model_audio=audio(sid, "model", 0),
                          tip="Primero imita el ritmo; después di la frase con tus propias palabras.",
                          items=[items[0]["id"]]))
        lessons.append({
            "id": f"{sid}-d4", "lang": lang, "level": "A1", "week": week, "day": 4,
            "unit": sid, "title": "Hablar sin miedo", "goal": "Responder con frases propias en la situación.",
            "tasks": tasks, "items": [items[9]["id"]],
        })

        # Day 5: read, write, review, checkpoint on the last unit.
        tasks = [
            task("reading", scene["reading"]["prompt"], text=scene["reading"]["text"],
                 choices=scene["reading"]["choices"], answer=str(scene["reading"]["answer"]),
                 explain="Vuelve al texto y busca la información exacta."),
            task("writing", scene["writing"]["prompt"], model=scene["writing"]["model"],
                 rubric=scene["writing"]["rubric"]),
            task("dictation", "Escucha y escribe la frase.", answer=scene["dialogue"][3]["text"],
                 audio=audio(sid, "line", 3), explain=scene["dialogue"][3]["es"]),
            vocab_choice(items[6], items, "to_es", sid + "-d5-1"),
            vocab_choice(items[8], items, "from_es", sid + "-d5-2"),
            vocab_choice(items[9], items, "to_es", sid + "-d5-3"),
            task("translation", f"Traduce al {LANGS[lang]}: «{scene['dialogue'][2]['es']}»",
                 answer=scene["dialogue"][2]["text"], explain="Compara con el modelo del diálogo."),
            task("review", "Repasa toda la unidad antes de cerrar la semana.",
                 items=[item["id"] for item in items]),
        ]
        tasks.append(vocab_choice(items[0], items, "to_es", sid + "-d5-4"))
        tasks.append(vocab_choice(items[4], items, "from_es", sid + "-d5-5"))
        tasks.append(vocab_choice(items[2], items, "from_es", sid + "-d5-6"))
        tasks.append(vocab_choice(items[5], items, "to_es", sid + "-d5-7"))
        tasks.append(task("cloze", data["cloze"][2][0], answer=data["cloze"][2][1], explain=data["cloze"][2][2]))
        tasks.append(task("speaking", "Cuenta en voz alta qué has aprendido en esta unidad.",
                          model=scene["turns"][-1]["model"], accepted=[scene["turns"][-1]["model"]],
                          tip="Usa al menos una palabra nueva y una frase completa.",
                          items=[items[9]["id"]]))
        if week == 5:
            tasks.insert(0, task("choice", "Repaso guiado A1: ¿qué frase pide algo con cortesía?",
                                 choices=["Ech hätt gär e Plooschter, wann ech gelift.", "Ech hunn e Plooschter.", "Wou ass e Plooschter?"],
                                 answer="0", explain="La fórmula cortés es Ech hätt gär ... wann ech gelift."))
        lessons.append({
            "id": f"{sid}-d5", "lang": lang, "level": "A1", "week": week, "day": 5,
            "unit": sid, "title": "Leer, escribir y cerrar" if week != 5 else "Repaso final A1",
            "goal": "Usar lo aprendido en lectura y escritura.",
            "tasks": tasks, "items": [], "checkpoint": week == 5,
        })

        units.append({
            "id": sid, "lang": lang, "level": "A1", "week": week,
            "title": course_title(scene["title"]), "can_do": scene["goal"], "scene": sid,
            "lessons": lessons,
        })

    roadmap = ROADMAP
    level_start = {stage["level"]: stage["start"] for stage in ROADMAP}
    level_order = {stage["level"]: index for index, stage in enumerate(ROADMAP)}

    grouped = {}
    for scene in generic_scenes:
        grouped.setdefault((scene["lang"], scene["level"]), []).append(scene)
    for (lang, level), level_scenes in sorted(
        grouped.items(), key=lambda entry: (entry[0][0], level_order.get(entry[0][1], 99))
    ):
        level_scenes.sort(key=lambda scene: (scene.get("course_week") or scene.get("week", 1), scene["id"]))
        # Scenes with an explicit course_week keep that week; the legacy five
        # seed units per level without one are spaced every five weeks using a
        # counter that only advances for them, so adding gap-filling weeks never
        # shifts the existing seed units.
        auto_index = 0
        for index, scene in enumerate(level_scenes):
            items = generic_items(scene)
            if not items:
                continue
            if scene.get("course_week"):
                week = scene["course_week"]
            elif level == "A1":
                week = scene.get("week")
            else:
                week = level_start.get(level, 1) + auto_index * 5
                auto_index += 1
            checkpoint = bool(scene.get("checkpoint")) or index == len(level_scenes) - 1
            units.append(build_generic_unit(scene, week, items, checkpoint))
            course_items.extend(items)

    units.sort(key=lambda unit: (unit["lang"], level_order.get(unit["level"], 99), unit["week"], unit["id"]))
    course = {"version": 1, "units": units, "items": course_items, "roadmap": roadmap}
    output = ROOT / "content" / "course.json"
    output.write_text(json.dumps(course, ensure_ascii=False, indent=1) + "\n")
    print(f"{output}: {len(units)} units, {sum(len(unit['lessons']) for unit in units)} lessons, {len(course_items)} items")


if __name__ == "__main__":
    build_course()
