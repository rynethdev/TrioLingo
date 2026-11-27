"""Author new A1 situations for weeks 6–20 in both main languages.

The source lines below are editable, not sentence permutations. Audio is generated
separately with generate-audio.py. Publication still needs native-speaker review.
"""
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# week, title, goal, reading question, three answers (correct first), writing prompt
TOPICS = [
    (6, "Hablar de tu familia", "Presenta a dos familiares y di dónde viven.", "¿Dónde vive la hermana?", ["En la ciudad", "En otra casa", "En el campo"], "Escribe dos frases sobre tu familia."),
    (7, "Describir tu casa", "Describe una habitación y pregunta por un objeto.", "¿Dónde está la llave?", ["En la mesa", "En la cocina", "En el bolsillo"], "Describe tu casa con dos frases."),
    (8, "Contar tu rutina", "Di cuándo te levantas y cómo vas al trabajo.", "¿A qué hora sale de casa?", ["A las ocho", "A las siete", "A las nueve"], "Escribe una rutina de mañana."),
    (9, "Hablar del tiempo", "Entiende el pronóstico y adapta un plan.", "¿Qué recomiendan llevar?", ["Una chaqueta", "Un paraguas", "Un sombrero"], "Escribe qué tiempo hace y qué harás."),
    (10, "Pedir en un restaurante", "Pide comida y una bebida con cortesía.", "¿Qué incluye el menú?", ["Una sopa", "Un postre", "Un café"], "Pide una comida y una bebida."),
    (11, "Tomar el autobús", "Pregunta por una parada y entiende un horario.", "¿Cuándo sale el próximo autobús?", ["A las nueve", "A las ocho", "A las diez"], "Pregunta cómo llegar a una parada."),
    (12, "Comprar ropa", "Pregunta por una talla y decide si te queda bien.", "¿Qué talla está disponible?", ["La mediana", "La pequeña", "La grande"], "Pide probarte una prenda de otra talla."),
    (13, "Seguir una dirección", "Pregunta por un lugar y sigue una indicación sencilla.", "¿Qué hay junto al museo?", ["El parque", "La estación", "La farmacia"], "Escribe cómo llegar a un lugar cercano."),
    (14, "Concertar una cita", "Pregunta por un día y confirma una hora.", "¿Qué día está cerrado?", ["El domingo", "El lunes", "El sábado"], "Propón una cita con día y hora."),
    (15, "Quedar con amigos", "Invita a alguien y acuerda dónde encontraros.", "¿Dónde se verán?", ["En la entrada", "En el café", "En la plaza"], "Invita a un amigo a una actividad."),
    (16, "Una mañana de trabajo", "Saluda a un colega y aclara una tarea.", "¿Dónde está la reunión?", ["En la sala pequeña", "En la cocina", "En casa"], "Escribe una pregunta breve a un colega."),
    (17, "Contar el fin de semana", "Di qué hiciste y haz una pregunta sencilla.", "¿Qué hizo el sábado?", ["Visitó a una amiga", "Trabajó", "Fue al cine"], "Cuenta dos cosas que hiciste."),
    (18, "Llegar a un alojamiento", "Da tu nombre y pregunta por la habitación.", "¿A qué hora se sirve el desayuno?", ["A las ocho", "A las siete", "A las nueve"], "Pregunta por la hora del desayuno."),
    (19, "Dejar un mensaje", "Di quién llama y pide que te devuelvan la llamada.", "¿Cuándo volverá la persona?", ["Por la tarde", "Por la mañana", "Mañana"], "Deja un mensaje con tu nombre."),
    (20, "Cerrar un día en la ciudad", "Resuelve un pequeño cambio de plan con cortesía.", "¿Qué cierra primero?", ["La tienda", "La estación", "El café"], "Explica un cambio de plan y propón una alternativa."),
]

# Each entry: four alternating dialogue lines (text, Spanish), an independent
# reading notice, a written model, and two lexical chunks (text, Spanish).
LB = {
    6: ([('Moien, hues du Geschwëster?', 'Hola, ¿tienes hermanos?'), ('Jo, ech hunn eng Schwëster.', 'Sí, tengo una hermana.'), ('Wou wunnt si?', '¿Dónde vive ella?'), ('Si wunnt hei an der Stad.', 'Vive aquí en la ciudad.')], 'Meng Schwëster wunnt an der Stad. Mir gesinn eis e Samschdeg.', 'Ech hunn eng Schwëster. Si wunnt an der Stad.', [('eng Schwëster', 'una hermana'), ('an der Stad', 'en la ciudad')]),
    7: ([('Wéi ass deng Wunneng?', '¿Cómo es tu piso?'), ('Si ass kleng, mee hell.', 'Es pequeño, pero luminoso.'), ('Wou ass d’Kichen?', '¿Dónde está la cocina?'), ('Si ass nieft der Stuff.', 'Está al lado del salón.')], 'De Schlëssel läit um Dësch. D’Kichen ass lénks.', 'Meng Wunneng ass kleng. D’Kichen ass nieft der Stuff.', [('kleng', 'pequeño'), ('nieft der Stuff', 'junto al salón')]),
    8: ([('Wéini stees du op?', '¿Cuándo te levantas?'), ('Ech stinn um siwen Auer op.', 'Me levanto a las siete.'), ('Wéi gees du op d’Aarbecht?', '¿Cómo vas al trabajo?'), ('Ech fuere mam Bus.', 'Voy en autobús.')], 'Ech ginn um aacht Auer aus dem Haus. De Bus kënnt um hallwer néng.', 'Ech stinn um siwen Auer op a fuere mam Bus.', [('um siwen Auer', 'a las siete'), ('mam Bus', 'en autobús')]),
    9: ([('Wéi ass d’Wieder haut?', '¿Qué tiempo hace hoy?'), ('Et ass kal an et reent.', 'Hace frío y llueve.'), ('Gees du an de Park?', '¿Vas al parque?'), ('Nee, ech bleiwen doheem.', 'No, me quedo en casa.')], 'Et ass haut kal. Huel eng Jackett mat, wann s du erausgees.', 'Et reent haut. Ech bleiwen doheem.', [('et reent', 'llueve'), ('ech bleiwen doheem', 'me quedo en casa')]),
    10: ([('Gudde Mëtteg, wat wëllt Dir iessen?', 'Buenas tardes, ¿qué desea comer?'), ('Ech hätt gär eng Zopp.', 'Querría una sopa.'), ('A wat wëllt Dir drénken?', '¿Y qué desea beber?'), ('E Waasser, wann ech gelift.', 'Un agua, por favor.')], 'De Menü huet eng Zopp an eng Zalot. D’Gedrénks kaschten extra.', 'Ech hätt gär eng Zopp an e Waasser, wann ech gelift.', [('eng Zopp', 'una sopa'), ('e Waasser', 'un agua')]),
    11: ([('Fiert dëse Bus an den Zentrum?', '¿Va este autobús al centro?'), ('Jo, awer eréischt an zéng Minutten.', 'Sí, pero dentro de diez minutos.'), ('Wou muss ech ausklammen?', '¿Dónde tengo que bajar?'), ('Bei der nächster Haltestell.', 'En la próxima parada.')], 'Den nächste Bus fiert um néng Auer. D’Haltestell ass virun der Schoul.', 'Fiert dëse Bus an den Zentrum? Wou muss ech ausklammen?', [('an den Zentrum', 'al centro'), ('d’nächst Haltestell', 'la próxima parada')]),
    12: ([('Hutt Dir dës Jackett a mëttlerer Gréisst?', '¿Tiene esta chaqueta en talla mediana?'), ('Jo, hei ass se.', 'Sí, aquí está.'), ('Kann ech se undoen?', '¿Puedo probármela?'), ('Natierlech. D’Kabinn ass do.', 'Por supuesto. El probador está allí.')], 'Déi mëttler Gréisst ass do. Déi grouss Gréisst ass ausverkaaft.', 'Hutt Dir dës Jackett a mëttlerer Gréisst? Kann ech se undoen?', [('dës Jackett', 'esta chaqueta'), ('d’Kabinn', 'el probador')]),
    13: ([('Entschëllegt, wou ass de Musée?', 'Disculpe, ¿dónde está el museo?'), ('Gitt riichtaus an dann no lénks.', 'Siga recto y luego a la izquierda.'), ('Ass et wäit vun hei?', '¿Está lejos de aquí?'), ('Nee, et dauert nëmme fënnef Minutten.', 'No, se tarda solo cinco minutos.')], 'De Musée ass nieft dem Park. Gitt bei der Bréck no lénks.', 'Gitt riichtaus an dann no lénks. De Musée ass no beim Park.', [('riichtaus', 'recto'), ('no lénks', 'a la izquierda')]),
    14: ([('Kënne mir eis e Freideg treffen?', '¿Podemos vernos el viernes?'), ('Jo, um dräi Auer?', 'Sí, ¿a las tres?'), ('Dat passt mir gutt.', 'Me viene bien.'), ('Also, bis e Freideg!', 'Entonces, ¡hasta el viernes!')], 'De Büro ass sonndes zou. Samschdes ass en bis mëttes op.', 'Kënne mir eis e Freideg um dräi Auer treffen?', [('e Freideg', 'el viernes'), ('um dräi Auer', 'a las tres')]),
    15: ([('Hues du e Samschdeg Zäit?', '¿Tienes tiempo el sábado?'), ('Jo, wat wëlls du maachen?', 'Sí, ¿qué quieres hacer?'), ('Komme mir an de Kino?', '¿Vamos al cine?'), ('Gär! Mir treffen eis virun der Entrée.', '¡Claro! Nos vemos frente a la entrada.')], 'De Film fänkt um siwen Auer un. Mir treffen eis virun der Entrée.', 'Hues du e Samschdeg Zäit? Mir kënnen an de Kino goen.', [('e Samschdeg', 'el sábado'), ('virun der Entrée', 'frente a la entrada')]),
    16: ([('Moien, wou ass d’Versammlung?', 'Hola, ¿dónde es la reunión?'), ('An deem klenge Sall um éischte Stack.', 'En la sala pequeña del primer piso.'), ('Wat soll ech matbréngen?', '¿Qué debo llevar?'), ('Deng Notizen, wann ech gelift.', 'Tus notas, por favor.')], 'D’Versammlung ass am klenge Sall. Bréng deng Notize mat.', 'Moien, wou ass d’Versammlung? Ech bréngen meng Notize mat.', [('d’Versammlung', 'la reunión'), ('meng Notizen', 'mis notas')]),
    17: ([('Wat hues du de Weekend gemaach?', '¿Qué hiciste el fin de semana?'), ('Ech hunn eng Frëndin besicht.', 'Visité a una amiga.'), ('War et flott?', '¿Estuvo bien?'), ('Jo, mir hunn zesumme gekacht.', 'Sí, cocinamos juntos.')], 'E Samschdeg hunn ech eng Frëndin besicht. E Sonndeg war ech doheem.', 'Ech hunn eng Frëndin besicht. Mir hunn zesumme gekacht.', [('de Weekend', 'el fin de semana'), ('zesumme gekacht', 'cocinado juntos')]),
    18: ([('Moien, ech hunn eng Reservatioun.', 'Hola, tengo una reserva.'), ('Op wéi engem Numm?', '¿A nombre de quién?'), ('Op den Numm García.', 'A nombre de García.'), ('Äert Zëmmer ass um zweete Stack.', 'Su habitación está en el segundo piso.')], 'De Kaffi gëtt um aacht Auer zerwéiert. Äert Zëmmer ass um zweete Stack.', 'Wéini gëtt de Kaffi zerwéiert? Ech hunn eng Reservatioun.', [('eng Reservatioun', 'una reserva'), ('Äert Zëmmer', 'su habitación')]),
    19: ([('Moien, kann ech mam Tom schwätzen?', 'Hola, ¿puedo hablar con Tom?'), ('Hien ass elo net do.', 'Ahora no está.'), ('Kann ech e Message hannerloossen?', '¿Puedo dejar un mensaje?'), ('Jo, ech soen him, datt Dir ugeruff hutt.', 'Sí, le diré que ha llamado.')], 'Den Tom kënnt haut de Mëtteg zeréck. Hannerloosst w.e.g. Är Nummer.', 'Moien, hei ass d’Ana. Kënnt Dir mech zeréckruffen?', [('e Message', 'un mensaje'), ('de Mëtteg', 'por la tarde')]),
    20: ([('De Buttek mécht gläich zou.', 'La tienda está a punto de cerrar.'), ('Da gi mir fir d’éischt dohin.', 'Entonces vamos allí primero.'), ('A wat maache mir duerno?', '¿Y qué hacemos después?'), ('Duerno drénke mir e Kaffi.', 'Después tomamos un café.')], 'De Buttek mécht um sechs Auer zou. De Café ass bis aacht Auer op.', 'De Buttek mécht zou. Mir ginn als éischt dohin an duerno an de Café.', [('fir d’éischt', 'primero'), ('duerno', 'después')]),
}

DA = {
    6: ([('Hej, har du søskende?', 'Hola, ¿tienes hermanos?'), ('Ja, jeg har en søster.', 'Sí, tengo una hermana.'), ('Hvor bor hun?', '¿Dónde vive ella?'), ('Hun bor her i byen.', 'Vive aquí en la ciudad.')], 'Min søster bor i byen. Vi ses på lørdag.', 'Jeg har en søster. Hun bor i byen.', [('en søster', 'una hermana'), ('i byen', 'en la ciudad')]),
    7: ([('Hvordan er din lejlighed?', '¿Cómo es tu piso?'), ('Den er lille, men lys.', 'Es pequeño, pero luminoso.'), ('Hvor er køkkenet?', '¿Dónde está la cocina?'), ('Det er ved siden af stuen.', 'Está al lado del salón.')], 'Nøglen ligger på bordet. Køkkenet er til venstre.', 'Min lejlighed er lille. Køkkenet er ved siden af stuen.', [('lille', 'pequeño'), ('ved siden af stuen', 'junto al salón')]),
    8: ([('Hvornår står du op?', '¿Cuándo te levantas?'), ('Jeg står op klokken syv.', 'Me levanto a las siete.'), ('Hvordan kommer du på arbejde?', '¿Cómo vas al trabajo?'), ('Jeg tager bussen.', 'Voy en autobús.')], 'Jeg går hjemmefra klokken otte. Bussen kommer halv ni.', 'Jeg står op klokken syv og tager bussen.', [('klokken syv', 'a las siete'), ('tager bussen', 'voy en autobús')]),
    9: ([('Hvordan er vejret i dag?', '¿Qué tiempo hace hoy?'), ('Det er koldt, og det regner.', 'Hace frío y llueve.'), ('Skal du i parken?', '¿Vas al parque?'), ('Nej, jeg bliver hjemme.', 'No, me quedo en casa.')], 'Det er koldt i dag. Tag en jakke med, hvis du går ud.', 'Det regner i dag. Jeg bliver hjemme.', [('det regner', 'llueve'), ('bliver hjemme', 'me quedo en casa')]),
    10: ([('Goddag, hvad vil du gerne spise?', 'Buenas tardes, ¿qué deseas comer?'), ('Jeg vil gerne have en suppe.', 'Querría una sopa.'), ('Og hvad vil du drikke?', '¿Y qué quieres beber?'), ('Et glas vand, tak.', 'Un vaso de agua, por favor.')], 'Menuen har en suppe og en salat. Drikkevarer koster ekstra.', 'Jeg vil gerne have en suppe og et glas vand, tak.', [('en suppe', 'una sopa'), ('et glas vand', 'un vaso de agua')]),
    11: ([('Kører denne bus til centrum?', '¿Va este autobús al centro?'), ('Ja, men først om ti minutter.', 'Sí, pero dentro de diez minutos.'), ('Hvor skal jeg stå af?', '¿Dónde tengo que bajar?'), ('Ved næste stoppested.', 'En la próxima parada.')], 'Den næste bus kører klokken ni. Stoppestedet er foran skolen.', 'Kører denne bus til centrum? Hvor skal jeg stå af?', [('til centrum', 'al centro'), ('næste stoppested', 'la próxima parada')]),
    12: ([('Har I denne jakke i medium?', '¿Tiene esta chaqueta en talla mediana?'), ('Ja, her er den.', 'Sí, aquí está.'), ('Må jeg prøve den?', '¿Puedo probármela?'), ('Selvfølgelig. Prøverummet er derovre.', 'Por supuesto. El probador está allí.')], 'Størrelse medium er på lager. Den store størrelse er udsolgt.', 'Har I denne jakke i medium? Må jeg prøve den?', [('denne jakke', 'esta chaqueta'), ('prøverummet', 'el probador')]),
    13: ([('Undskyld, hvor ligger museet?', 'Disculpe, ¿dónde está el museo?'), ('Gå ligeud og derefter til venstre.', 'Siga recto y luego a la izquierda.'), ('Er det langt herfra?', '¿Está lejos de aquí?'), ('Nej, det tager kun fem minutter.', 'No, se tarda solo cinco minutos.')], 'Museet ligger ved siden af parken. Drej til venstre ved broen.', 'Gå ligeud og drej til venstre. Museet ligger ved parken.', [('ligeud', 'recto'), ('til venstre', 'a la izquierda')]),
    14: ([('Kan vi mødes på fredag?', '¿Podemos vernos el viernes?'), ('Ja, klokken tre?', 'Sí, ¿a las tres?'), ('Det passer mig godt.', 'Me viene bien.'), ('Så ses vi på fredag!', 'Entonces, ¡hasta el viernes!')], 'Kontoret er lukket om søndagen. Om lørdagen er der åbent til middag.', 'Kan vi mødes på fredag klokken tre?', [('på fredag', 'el viernes'), ('klokken tre', 'a las tres')]),
    15: ([('Har du tid på lørdag?', '¿Tienes tiempo el sábado?'), ('Ja, hvad vil du lave?', 'Sí, ¿qué quieres hacer?'), ('Skal vi gå i biografen?', '¿Vamos al cine?'), ('Gerne! Vi mødes foran indgangen.', '¡Claro! Nos vemos frente a la entrada.')], 'Filmen starter klokken syv. Vi mødes foran indgangen.', 'Har du tid på lørdag? Vi kan gå i biografen.', [('på lørdag', 'el sábado'), ('foran indgangen', 'frente a la entrada')]),
    16: ([('Hej, hvor er mødet?', 'Hola, ¿dónde es la reunión?'), ('I det lille lokale på første sal.', 'En la sala pequeña del primer piso.'), ('Hvad skal jeg tage med?', '¿Qué debo llevar?'), ('Dine noter, tak.', 'Tus notas, por favor.')], 'Mødet er i det lille lokale. Tag dine noter med.', 'Hej, hvor er mødet? Jeg tager mine noter med.', [('mødet', 'la reunión'), ('mine noter', 'mis notas')]),
    17: ([('Hvad lavede du i weekenden?', '¿Qué hiciste el fin de semana?'), ('Jeg besøgte en veninde.', 'Visité a una amiga.'), ('Var det hyggeligt?', '¿Estuvo bien?'), ('Ja, vi lavede mad sammen.', 'Sí, cocinamos juntos.')], 'Om lørdagen besøgte jeg en veninde. Om søndagen var jeg hjemme.', 'Jeg besøgte en veninde. Vi lavede mad sammen.', [('i weekenden', 'el fin de semana'), ('lavede mad sammen', 'cocinamos juntos')]),
    18: ([('Hej, jeg har en reservation.', 'Hola, tengo una reserva.'), ('Hvilket navn står reservationen i?', '¿A nombre de quién está la reserva?'), ('Den står i navnet García.', 'Está a nombre de García.'), ('Dit værelse er på anden sal.', 'Su habitación está en el segundo piso.')], 'Morgenmaden serveres klokken otte. Dit værelse er på anden sal.', 'Hvornår serveres morgenmaden? Jeg har en reservation.', [('en reservation', 'una reserva'), ('dit værelse', 'su habitación')]),
    19: ([('Hej, må jeg tale med Tom?', 'Hola, ¿puedo hablar con Tom?'), ('Han er her ikke lige nu.', 'Ahora no está.'), ('Må jeg lægge en besked?', '¿Puedo dejar un mensaje?'), ('Ja, jeg siger, at du har ringet.', 'Sí, le diré que has llamado.')], 'Tom kommer tilbage i eftermiddag. Læg venligst dit nummer.', 'Hej, det er Ana. Kan du ringe tilbage?', [('en besked', 'un mensaje'), ('i eftermiddag', 'por la tarde')]),
    20: ([('Butikken lukker snart.', 'La tienda está a punto de cerrar.'), ('Så går vi derhen først.', 'Entonces vamos allí primero.'), ('Og hvad gør vi bagefter?', '¿Y qué hacemos después?'), ('Bagefter drikker vi en kop kaffe.', 'Después tomamos un café.')], 'Butikken lukker klokken seks. Caféen har åbent til klokken otte.', 'Butikken lukker snart. Vi går derhen først og bagefter på café.', [('først', 'primero'), ('bagefter', 'después')]),
}


def build():
    scenes = []
    for lang, material in (("lb", LB), ("da", DA)):
        if set(material) != set(range(6, 21)):
            raise ValueError(f"Missing A1 weeks for {lang}")
        for week, title, goal, question, choices, writing_prompt in TOPICS:
            lines, reading, written, vocabulary = material[week]
            sid = f"{lang}-a1-w{week:02d}"
            def shuffled(values, suffix):
                options = list(values)
                random.Random(sid + suffix).shuffle(options)
                return options, options.index(values[0])
            heard_options, heard_answer = shuffled(
                [lines[3][1], lines[1][1], lines[0][1]], "listen")
            read_options, read_answer = shuffled(choices, "read")
            scenes.append({
                "id": sid, "lang": lang, "level": "A1", "week": week,
                "title": title, "goal": goal, "setup": goal,
                "dialogue": [{"speaker": i % 2, "text": text, "es": es}
                             for i, (text, es) in enumerate(lines)],
                "listening": {"prompt": "¿Qué dice la última persona?", "choices":
                              heard_options, "answer": heard_answer},
                "turns": [{"prompt": lines[i][0], "es": f"Responde: {lines[i+1][1]}",
                           "model": lines[i+1][0], "model_es": lines[i+1][1],
                           "accepted": [], "tip": "Escucha el modelo y responde con una frase completa."}
                          for i in (0, 2)],
                "reading": {"text": reading, "prompt": question,
                            "choices": read_options, "answer": read_answer},
                "writing": {"prompt": writing_prompt, "model": written,
                            "rubric": "Incluye la información solicitada con una frase clara."},
                "exercises": [{"kind": "vocabulary", "prompt": f"¿Cómo se dice «{es}» en esta escena?",
                               "answer": text, "explanation": f"{text} = {es}."}
                              for text, es in vocabulary],
                "editorial_status": "pendiente de revisión por hablante competente",
            })
    output = ROOT / "content/a1-expansion.json"
    output.write_text(json.dumps(scenes, ensure_ascii=False, indent=1) + "\n")
    print(f"{output}: {len(scenes)} new A1 scenes")


if __name__ == "__main__":
    build()
