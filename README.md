# Idiomas

Webapp local para estudiar luxemburgués y danés de A1 a C2, con interfaz en español. Hay **200 unidades y 1.000 lecciones por idioma** (semanas 1–200 sin huecos), con 12–16 tareas por lección y repaso espaciado de expresiones. Las 136 semanas B1–C2 añadidas, más las semanas A1 6–20 y A2 intermedias, son **borradores originales pendientes de revisión por hablantes competentes** (170 por idioma). La hoja de ruta propone unas 1.000 horas por idioma: que las 200 casillas tengan material no significa que se hayan impartido ni medido esas horas, ni que haya validación pedagógica o acreditación de nivel. Francés permanece como práctica secundaria.

## Abrir en el Mac

Abre **dist/Abrir Idiomas.command** con doble clic y mantén abierta la ventana del servidor mientras estudias. También puedes iniciarla desde la raíz del proyecto:

```sh
./dist/idiomas --open
```

El navegador abre [http://localhost:8787](http://localhost:8787). Selecciona el idioma y comienza por **Hoy**. En **Curso** puedes consultar las unidades disponibles de cada nivel.

## Cómo estudiar cada semana

1. En **Hoy**, abre la siguiente lección. Cada unidad ofrece cinco días de escucha, vocabulario, gramática, habla y lectura/escritura. Retoma una lección a partir de la primera tarea pendiente.
2. Escucha los MP3, responde las preguntas, escribe los dictados y compara tus respuestas orales o escritas con los modelos. Puedes grabarte y revisar la transcripción local. La coincidencia literal no sustituye una evaluación humana de pronunciación o redacción.
3. Al terminar una lección, sus expresiones entran en **Vocabulario**. Repasa las tarjetas vencidas y califica tu recuerdo; los intervalos se ajustan por tarjeta. **Repaso** conserva también los ejercicios del itinerario anterior.
4. Usa **Práctica** para simulaciones, controles y pronunciación. Todas las semanas tienen escenas y texto; muchas redacciones y la mayoría de las semanas B1–C2 son borradores que requieren revisión externa.

**Cobertura actual:** 200 de 200 semanas y 1.228 tarjetas por idioma, de las cuales 170 semanas por idioma son borradores sin revisar. Los controles guiados no equivalen a pruebas independientes ni acreditan nivel. El audio de las semanas B1–C2 se está terminando de sintetizar; mientras falte algún MP3, esa lección lo indicará. La sección **Progreso** mide solo el tiempo activo comunicado por las lecciones desde la actualización que introdujo esa medición; no convierte las tareas anteriores en horas ficticias.

## Progreso y grabaciones en este Mac

Los modelos de transcripción están en `dist/voices/`. La app y la transcripción local funcionan sin conexión. Recuerda que puedes escucharte aunque el modelo de transcripción esté ausente.

Pulsa **Guardar en Mis grabaciones** si quieres conservar un audio para compararlo con tu progreso más adelante. Puedes reproducir, comparar o borrar cada toma desde **Mis grabaciones**. Las grabaciones y el progreso viven en `~/Library/Application Support/Idiomas/progress.sqlite3`. Las grabaciones se conservan al cerrar la app. La base guarda resultados y fechas de repaso. Los textos que escribes o transcribes se usan durante el intento. Copia la base de datos con Idiomas cerrado si quieres guardar un respaldo.

El panel distingue los aciertos observables, la repetición exacta y tu valoración de las respuestas abiertas. El historial de una instalación anterior mantiene las actividades completadas. Los resultados detallados se guardan desde esta edición. Las pruebas internas son práctica orientada por el MCER.

## Conversación libre

La conversación libre devuelve respuestas escritas y correcciones de texto. Para activarla, configura `OPENAI_API_KEY` en el entorno del servidor, arranca la aplicación desde ese entorno y activa la opción en **Ajustes**. La app envía la respuesta confirmada y hasta tres turnos recientes a la API de OpenAI. El flujo guiado acepta las variantes previstas y, para las respuestas abiertas, muestra un ejemplo y criterios de autoevaluación.

## Desarrollo

Con Rust estable, herramientas de línea de comandos de Xcode y CMake instalados, ejecuta:

```sh
./scripts/package-mac.sh
```

Para reconstruir los modelos y los MP3, instala también Python 3.11, uv y FFmpeg y ejecuta `./scripts/prepare-voice.sh` antes de empaquetar. Las escenas originales están en `content/scenes.json`, las semanas adicionales en `content/itinerary.json` y los borradores se editan en `scripts/build-a1-expansion.py`, `scripts/build-a2-expansion.py` y `scripts/build-upper-expansion.py` (B1–C2). Tras cambiar su contenido, genera escenas y audio con el `build-*-expansion.py` correspondiente y `.build/voice-env/bin/python scripts/generate-audio.py --a1-expansion --missing lb da` (o `--a2-expansion` / `--upper-expansion`); después regenera el curso y empaqueta. Si modificas texto de una escena que ya tiene MP3, regenera su audio con `--scene ID lb` o `--scene ID da` sin `--missing`.

> **Audio B1–C2 en curso:** la síntesis de las 272 escenas nuevas quedó a medias por presión de memoria del sistema. Complétala con `.build/voice-env/bin/python scripts/generate-audio.py --upper-expansion --missing lb da` (reaprovecha lo ya generado). Hasta entonces la auditoría reportará *audio ausente*.

Antes de publicar contenido nuevo, ejecuta `python3 scripts/build-course.py`, `python3 scripts/audit-course.py` y `cargo test`. La auditoría comprueba integridad, audio y cobertura, y avisa de la repetición editorial. No sustituye la revisión por hablantes competentes ni las pruebas con alumnos. La estructura de 200 semanas por idioma ya está cubierta con borradores; para completar el plan de verdad faltan la revisión lingüística de los 170 borradores por idioma, el pilotaje con estudiantes, evaluaciones con situaciones no vistas y una ruta profesional adaptada al sector laboral del estudiante. No marques esas semanas como validadas antes de su revisión.

- `IDIOMAS_PORT` cambia el puerto local.
- `IDIOMAS_DATA_DIR` permite usar una carpeta de progreso distinta.
- `IDIOMAS_VOICES_DIR` permite indicar otra carpeta de modelos de voz.

## Créditos

- Audio sintético en luxemburgués generado con [VITS2 Claude](https://huggingface.co/ZLSCompLing/VITS2-Claude), del Zenter fir d’Lëtzebuerger Sprooch, con licencia MIT.
- Audio sintético en danés generado con [Piper Talesyntese](https://huggingface.co/rhasspy/piper-voices/blob/main/da/da_DK/talesyntese/medium/MODEL_CARD).
- Transcripción en luxemburgués con [LuxASR Base](https://huggingface.co/unilux/whisper-base-v1-luxembourgish), de la Universidad de Luxemburgo, con licencia OpenMDW 1.1. El paquete convierte y cuantiza el modelo.
- Transcripción en danés con [Whisper Small Danish](https://huggingface.co/thorhojhus/whisper-small-danish), cuantizado a Q5_1 y con licencia MIT. Los avisos van en `dist/voices/da-NOTICES.md`.
- Niveles orientados por los [descriptores del MCER](https://www.coe.int/en/web/common-european-framework-reference-languages/cefr-descriptors-search).
