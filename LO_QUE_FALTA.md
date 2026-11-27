# Idiomas: qué es, qué existe y qué falta para terminarlo de verdad

> **Estado de este documento:** traspaso técnico y editorial, no certificado de nivel ni promesa de que el curso esté completo. Describe el repositorio tal como está ahora. Si cambian los datos, volver a calcular las cifras con `scripts/audit-course.py` antes de repetirlas.

## 1. Encargo y definición de «terminado»

**Idiomas** es una aplicación local para aprender **luxemburgués (`lb`) y danés (`da`) desde cero hasta un desempeño profesional**, con interfaz en español y francés (`fr`) como práctica secundaria. La meta acordada es **200 semanas, 1.000 lecciones y alrededor de 1.000 horas de práctica real por cada idioma**, en una progresión A1 → A2 → B1 → B2 → C1 → C2 deliberadamente lenta. No son 1.000 horas entre los dos idiomas. Cada semana se organiza en cinco días, pero cinco lecciones breves no equivalen por sí solas a cinco horas de estudio.

«Completar el curso» significa, como mínimo, que **cada una de las 200 semanas por idioma tiene contenido propio y utilizable**, que los textos y audios corresponden al material efectivamente servido, que las habilidades de comprensión, interacción y producción aumentan con el nivel, que existen evaluaciones con material *no visto*, que se puede usar sin conexión salvo funciones opcionales claramente identificadas, y que un estudiante puede continuar sin perder su progreso ni sus grabaciones. **Desempeño profesional** añade tareas laborales extensas y adaptadas al sector, feedback humano cuando la tarea no puede calificarse automáticamente y evidencia independiente del desempeño; no se obtiene sumando tarjetas, rellenando huecos con variaciones de las mismas frases ni aprobando preguntas cuyas respuestas se acaban de mostrar.

El usuario pidió explícitamente **contenido real**, no una hoja de ruta disfrazada de curso. No sustituir escenas, lecturas, audios y producción nueva por cambios de métricas o por promesas. Tampoco afirmar que el curso está completo si falta revisión lingüística o validación pedagógica. La interfaz puede mostrar el mapa de 200 semanas, pero debe distinguirlo de las semanas que de verdad tienen material y de las que son borradores.

## 2. Estado comprobado del repositorio

| Nivel | Semanas previstas | Semanas con material por idioma | Semanas que faltan por idioma | Horas acumuladas objetivo* |
| --- | ---: | ---: | ---: | ---: |
| A1 | 1–20 (20) | 20 | 0 | 100 |
| A2 | 21–44 (24) | 24 | 0 | 220 |
| B1 | 45–80 (36) | 36 | 0 | 400 |
| B2 | 81–116 (36) | 36 | 0 | 580 |
| C1 | 117–158 (42) | 42 | 0 | 790 |
| C2 | 159–200 (42) | 42 | 0 | 1.000 |
| **Total** | **200** | **200** | **0** | **1.000** |

\* Los hitos de horas son **metas acumuladas**, no horas ya impartidas ni medidas. La aplicación mide el tiempo activo comunicado por las lecciones desde que se añadió esa función; no debe convertir automáticamente tareas antiguas en horas ficticias. **Que las 200 casillas tengan material no significa que se hayan impartido ni medido esas 1.000 horas.**

Por idioma hay ahora **200 unidades, 1.000 lecciones (cinco por unidad) y 1.228 tarjetas**: **2.000 lecciones entre ambos idiomas**, sin huecos entre las semanas 1 y 200. Las **136 semanas que antes faltaban por idioma** (B1 31, B2 31, C1 37, C2 37) se han redactado como situaciones nuevas y distintas —narración, reclamaciones, citas, reuniones, correos con registro, negociación, mediación, documentación, incertidumbre, ironía, síntesis de fuentes y un *capstone*— en `scripts/build-upper-expansion.py`, con traducción al español y audio local. Las cinco unidades semilla de cada nivel superior **no se movieron**: conservan sus semanas (45/50/55/60/65, etc.). Estas cifras describen la **estructura cubierta**, no una medida de suficiencia didáctica ni de dominio.

Todas las semanas nuevas de B1–C2 llevan `editorial_status: "pendiente de revisión por hablante competente"`. Sumadas a los 34 borradores previos de A1/A2, hay ahora **170 borradores por idioma**: solo quedan como **revisadas** las semanas que ya lo estaban antes. La auditoría devuelve **0 huecos de cobertura** y **12 avisos de repetición editorial** (dos idiomas × seis niveles); esos avisos importan y siguen pendientes: muchas tareas derivadas reutilizan consignas genéricas, y la integridad técnica no demuestra variedad, duración ni dominio lingüístico. Las pruebas Python de expansión (incluida la nueva `tests/test_upper_expansion.py`, que verifica continuidad 1–200 y que los borradores no desplazan las semillas) y las pruebas Rust pasaron en la última verificación; **no sustituyen revisión humana ni ensayos con estudiantes**.

> **Audio pendiente de completar.** La síntesis de los MP3 de las 272 escenas nuevas (≈2.448 clips) quedó **a medias** (≈926 generados; el luxemburgués casi completo, el danés apenas iniciado) porque el proceso se interrumpió por presión de memoria del sistema. Hasta terminarla, `scripts/audit-course.py` reporta errores de *audio ausente* (no estructurales). Para completarla: `.build/voice-env/bin/python scripts/generate-audio.py --upper-expansion --missing lb da` (regenera solo lo que falta). La auditoría quedará sin errores cuando todos los clips existan.

La aplicación empaquetada se ejecuta en `http://localhost:8787/`; el ejecutable es `dist/idiomas`. Las semanas A2 nuevas ya están instaladas. La base real del usuario está en `~/Library/Application Support/Idiomas/progress.sqlite3`; **no borrarla ni usarla para pruebas**. El contenido y los MP3 se incrustan en el binario al compilar, de modo que editar JSON, JavaScript o audio no actualiza por sí solo un proceso ya en marcha. La función **Hoy** se detiene al llegar a un hueco de semanas y no debe saltarlo silenciosamente; **Curso** permite explorar bloques posteriores sin acreditarlos.

## 3. Mapa del código: dónde se cambia cada cosa

| Ruta | Responsabilidad y precaución |
| --- | --- |
| `content/scenes.json`, `content/itinerary.json` | Escenas originales y bloques previos. Conservar IDs y orden de progreso. |
| `scripts/build-a1-expansion.py`, `scripts/build-a2-expansion.py` | **Fuentes editables** de las escenas añadidas; generan `content/a1-expansion.json` y `content/a2-expansion.json`. Editar la fuente, no solo el JSON derivado. |
| `scripts/build-upper-expansion.py` | **Fuente editable** de las 136 semanas B1–C2 por idioma; genera `content/upper-expansion.json`. Cada unidad fija `course_week` explícito para no desplazar las cinco semillas del nivel. Es el sitio donde corregir texto tras la revisión por hablantes competentes; editar aquí, no el JSON derivado. |
| `scripts/build-course.py` | Combina esas fuentes, asigna semana y cinco lecciones, crea tareas y tarjetas en `content/course.json`. `ROADMAP` define los rangos y las metas acumuladas. El relleno automático de tareas no aporta por sí mismo un temario original. Para nuevos niveles hay que incorporar explícitamente sus fuentes al `build_course()`. |
| `content/course.json` | Artefacto generado que el backend incrusta con `include_str!`. No usarlo como única fuente editorial. |
| `scripts/generate-audio.py` | Genera MP3 en `web/audio/` con síntesis local; acepta `--a1-expansion`, `--a2-expansion`, `--missing`, `--force-scenes` y `--scene`. Para nuevos bloques habrá que ampliar la selección de archivos. `--missing` no actualiza audio de frases ya modificadas si el archivo existe. |
| `web/audio/` | Audio servido offline e incrustado en el ejecutable. Comprobar la correspondencia **texto ↔ MP3**, no solo que el archivo existe. |
| `scripts/audit-course.py` | Detecta IDs duplicados, referencias y audio ausente, opciones inválidas, 12–16 tareas por lección, continuidad A1/A2 y repetición de consignas. Actualmente **no verifica aún la continuidad completa de B1–C2, la calidad de traducción, la duración pedagógica ni la independencia de exámenes**. |
| `tests/test_a1_expansion.py`, `tests/test_a2_expansion.py` | Pruebas de continuidad y variedad mínima. Al ampliar niveles, añadir pruebas específicas; no limitarse a cambiar números esperados. |
| `src/main.rs`, `src/learning.rs` | Servidor Rust/Axum, API `/api/course`, `/api/today`, `/api/lesson/{id}`, respuesta de tareas y SRS. `main.rs` incrusta `content/course.json` y `web/`; las escenas del catálogo anterior se cargan por separado. Si un nuevo bloque debe estar también en las simulaciones de **Práctica**, conectar sus escenas al catálogo correspondiente, no asumir que figurar en el curso basta. |
| `src/progress.rs` | SQLite: intentos, lecciones, tarjetas, minutos y grabaciones. Preservar IDs y migraciones. La escritura libre no es una corrección humana ni una puntuación automática fiable. |
| `src/voice.rs`, `web/recorder.js`, `web/audio.js` | Grabación y transcripción local. Mantener grabaciones reproducibles y el camino sin modelo de transcripción; no exigir conexión a Internet. |
| `web/course.js`, `web/app.js`, `web/field*.js` | Pantallas Hoy/Curso/lección y práctica. Etiquetas de borrador, cobertura y huecos deben reflejar datos reales; evitar cifras fijas y títulos que sugieran certificación. |
| `content/french.json` | Francés secundario; no confundir sus actividades con las 200 semanas **de cada idioma principal**. |
| `scripts/package-mac.sh`, `scripts/prepare-voice.sh` | El primero regenera A1/A2, prueba, audita y compila para macOS arm64. **No sintetiza audio nuevo automáticamente**. El segundo prepara dependencias/modelos y puede reconstruir voz; requiere Python 3.11, `uv`, FFmpeg y herramientas de compilación. |
| `dist/`, `.build/` | Distribución y trabajo local. No tratar archivos temporales o resultados de pruebas como fuente de verdad. |

**Persistencia:** el servidor usa SQLite en `~/Library/Application Support/Idiomas/`, salvo `IDIOMAS_DATA_DIR`. Se pueden cambiar `IDIOMAS_PORT` e `IDIOMAS_VOICES_DIR`. La app local y sus audios funcionan sin red; **conversación libre** es una función opcional que usa OpenAI cuando el usuario configura `OPENAI_API_KEY` y la activa. No presentarla como offline. Las grabaciones viven en la base SQLite; antes de una migración sensible, respaldarla con la app cerrada.

## 4. Trabajo editorial pendiente por nivel

### B1: 31 semanas por idioma (el siguiente hueco)

Completar **45–80** sin mover las cinco unidades existentes. Diseñar secuencias de narración en pasado y futuro, planes con cambios, experiencias laborales, causas y consecuencias, preferencias justificadas, reclamaciones, citas y trámites menos previsibles, noticias locales y comprensión de voces distintas. Cada semana debe terminar en una acción comprobable: dejar un mensaje útil, explicar un incidente, comparar soluciones, responder a un correo o resolver un imprevisto **sin copiar el diálogo**. Introducir lenguaje profesional transversal: turnos, instrucciones, plazos, seguridad, solicitudes de aclaración y feedback a colegas. Grabar versiones a velocidad natural y, donde sea pedagógicamente útil, apoyos más lentos. Construir al menos un control de fin de bloque con materiales desconocidos.

### B2: 31 semanas por idioma

Completar **81–116**. Planificar reuniones, correos con tono apropiado, informes breves, negociación de prioridades, discrepancias con evidencia, interpretación de instrucciones ambiguas, conversación sostenida y lectura de textos auténticos o adaptados con derechos claros. El desempeño no se evalúa con una única frase: pedir propuestas, réplicas, acuerdos, síntesis y revisión de lo escrito. Introducir variantes de registro y voces/contextos; marcar cualquier uso de material auténtico con fuente, permiso y fecha. Separar el núcleo profesional común de los itinerarios sectoriales elegidos por el estudiante.

### C1: 37 semanas por idioma

Completar **117–158**. Argumentación larga y precisa, matiz, cortesía estratégica, mediación de posiciones, documentación compleja, incertidumbre, corrección de malentendidos, exposiciones y edición de textos propios. Usar textos y audios sustancialmente más largos que en A1/A2 y tareas abiertas con rúbricas analíticas. Incluir transferencia entre formatos: de una reunión a un resumen, de datos a una recomendación, de una crítica implícita a una respuesta diplomática. Revisar la naturalidad de registros y los límites de cada contexto profesional.

### C2: 37 semanas por idioma

Completar **159–200** con integración flexible de fuentes, estilo, ironía, implicaturas, escritura especializada, mediación bajo presión y capstone profesional. No afirmar equivalencia C2 por completar tareas guiadas: exigir evaluación de comprensión de materiales nuevos, interacción en tiempo real y producción escrita/oral valorada por personas competentes. Definir criterios transparentes de coherencia, precisión, adecuación al interlocutor, autonomía y recuperación ante malentendidos. La disponibilidad de examinadores y de estudiantes para pilotaje es una dependencia **externa**, no algo que el generador de JSON pueda resolver.

### Ruta profesional: transversal, no un apéndice cosmético

No se conoce aquí el sector laboral del estudiante. Diseñar un **núcleo común** aplicable a empleo real y un **selector opcional de contexto/sector** (por ejemplo, atención al público, oficina/administración u oficio técnico, sujeto a investigación y elección del usuario). Reutilizar la habilidad, **no la misma frase**: «negociar un plazo» puede practicarse con un cliente, un compañero y una administración mediante datos, documentos, consecuencias y registros distintos. Si se añade personalización, conservar un camino completo sin configuración ni Internet. En campos regulados —salud, derecho, seguridad— validar terminología y añadir límites; no convertir ejemplos inventados en instrucciones profesionales o asesoramiento.

## 5. Especificación de una semana con contenido verdadero

Antes de escribir, registrar para cada idioma y semana: `level`, `week`, ID estable, prerrequisitos, objetivo MCER observado (no acreditado), propósito comunicativo, entorno, interlocutores, registro, formas lingüísticas nuevas, expresiones de repaso, materiales, dificultad, tiempo de estudio estimado **desglosado**, criterios de evaluación y estado editorial. Preparar un **mapa de dependencias**: qué se introdujo, qué se recupera después de 1/3/7/21 días y qué se necesita antes del siguiente bloque. No repetir unidades solo para llenar 200 casillas.

Un ejemplo de cinco días —**estructura flexible**, no plantilla para producir escenas idénticas—:

1. **Encuentro y comprensión:** audio con una situación y un objetivo real, predicción, escucha global y detalles, transcripción/ayuda después del primer intento. Los distractores deben ser plausibles y específicos, no la primera o última línea obvia.
2. **Vocabulario y transferencia:** expresiones nuevas contextualizadas, contraste con expresiones similares, recuperación activa y una situación diferente que obligue a escoger la forma adecuada. Añadir ejemplos con audio, no inflar tarjetas duplicando todo el diálogo.
3. **Estructuras con significado:** explicar una construcción, contrastar alternativas, corregir errores frecuentes y usarla en un mensaje nuevo. Los huecos automáticos en la palabra más larga de una frase **no constituyen** una progresión gramatical.
4. **Interacción y producción oral:** interlocutor con información que el estudiante no conoce, variantes de respuesta y reparación; grabación local, repetición con propósito y autoevaluación guiada. ASR o coincidencia literal no equivalen a evaluación de inteligibilidad o pronunciación.
5. **Lectura, escritura y cierre:** texto independiente del diálogo, pregunta inferencial o de aplicación, escritura con destinatario real, revisión de borrador y tarea de transferencia o control breve con contenido no visto. Dar modelos y rúbricas, no marcar una respuesta abierta como «dominada» solo porque se envió.

El objetivo aproximado de **5 horas por semana** tiene que sostenerse mediante actividades reales —lectura y escucha extensiva, preparación, producción, corrección y repaso— con estimaciones observables. Hoy una unidad suele derivarse de una escena breve de cuatro líneas y tareas derivadas; **no deducir cinco horas de contar cinco pantallas o 65 clics**. Si la semana no da suficiente práctica, escribir materiales adicionales: segundo diálogo con giro, lectura más larga, audio de otra voz, documento, tarea de proyecto y material de repaso. Preferir calidad y variedad auténtica a cantidad de botones.

**Dinámica pedagógica:** variar la información y el desenlace entre intentos, introducir decisiones con consecuencias, tareas por roles, información incompleta, recuperación espaciada y rutas de apoyo que desaparecen gradualmente. Ofrecer ayudas al atascarse; no desbloquear una acreditación a partir de una repetición guiada. Los escenarios alternativos deben ser textos redactados y revisados, **no permutaciones de nombres, horas o sustantivos sobre una única frase**. Mantener accesibilidad (transcripción, controles de audio, teclado, contraste y opción de repetir sin penalización) y uso sin conexión. Variación y adaptación no deben alterar la identidad de una tarea ya iniciada ni romper el progreso al actualizar.

## 6. Flujo correcto para crear y publicar cada bloque

### A. Planificar antes de generar

1. Elegir un bloque **consecutivo** de semanas faltantes (B1 primero) y escribir una matriz por semana de situación, función, registro, gramática, léxico, medio, productos oral/escrito y objetivos de repaso. Revisar que no duplican la misma escena de A1/A2 con otro título. Definir anticipadamente qué se evaluará de modo independiente.
2. Redactar en **ambas lenguas** el contenido específico con traducción española cuidada. Para B2–C2, producir materiales más largos y variados; evitar una «semana C2» compuesta solo de cuatro réplicas y tres opciones de lectura. Conservar evidencia de fuentes/licencias cuando se adapte material externo.
3. Pasar una revisión editorial preliminar: ortografía y diacríticos, formalidad/informalidad coherente, concordancia, traducción semántica, naturalidad, instrucciones que correspondan a la escena y respuestas justificables. Someter el bloque a **hablantes competentes de cada idioma**; registrar correcciones y el nombre/fecha o referencia de la revisión. Si no se ha revisado, marcarlo como borrador, no omitir el estado.

### B. Integrar sin perder datos

4. Crear una fuente editable nueva siguiendo el patrón de `scripts/build-a2-expansion.py` y generar su JSON derivado. Añadirla a `scripts/build-course.py`, `scripts/generate-audio.py` y `scripts/package-mac.sh`; si sus escenas se necesitan en Práctica, revisar también la carga de catálogo de `src/main.rs`. Mantener `lang`, `level`, `week`/`course_week`, `id`, `dialogue`, `listening`, `turns`, `reading`, `writing`, `exercises` y `editorial_status` coherentes con el generador. Para unidades intercaladas, asignar la semana **explícitamente**, no confiar en un índice que pueda desplazar unidades existentes.
5. **Congelar IDs existentes** de unidades, lecciones, tarjetas y tareas ya iniciadas; no renumerar semanas previas ni cambiar silenciosamente el orden/clave de una tarea en una lección con progreso. Si hace falta reestructurar una unidad, versionar/migrar el progreso y probarlo con una copia de una base anterior. No borrar ni sobrescribir `progress.sqlite3` real, ni grabaciones ni repasos.
6. Generar audio local por idioma y bloque. Para los bloques actuales:

   ```sh
   python3 scripts/build-a1-expansion.py
   python3 scripts/build-a2-expansion.py
   python3 scripts/build-course.py
   .build/voice-env/bin/python scripts/generate-audio.py --a2-expansion --missing lb da
   ```

   En un bloque futuro, actualizar las banderas/archivos en el script de audio antes de usar un comando equivalente. Al editar una frase que ya tenga MP3, usar `--force-scenes ID1,ID2` con la selección de bloque e idioma apropiada: `--missing` **solo** no regenera ese clip. No lanzar síntesis simultáneas sobre los mismos nombres. Verificar manualmente una muestra de audio/texto y la pronunciación con hablantes; la presencia de MP3 no garantiza que diga lo correcto. Todo audio requerido debe empaquetarse y servir `audio/mpeg` sin conexión.

### C. Probar antes de instalar

7. Ejecutar, en este orden después de generar el contenido y el audio, `python3 -m unittest discover -s tests -p 'test_*.py'`, `python3 scripts/audit-course.py`, `cargo test` y `node --input-type=module --check < web/course.js` si cambió la interfaz. Ampliar la auditoría para verificar rangos y números exactos **B1–C2**, unicidad `lang`+semana, integridad y duración de archivos, estabilidad de IDs, longitud y procedencia de textos, calidad de distractores, equilibrio de respuestas, y que los tests con datos no vistos no aparezcan filtrados en modelos previos. Registrar y resolver los avisos de repetición; nunca rebajar umbrales solo para obtener verde.
8. Hacer pruebas de integración en una **base temporal** mediante `IDIOMAS_DATA_DIR` e `IDIOMAS_PORT` distintos. Verificar `/api/course?lang=lb|da`, `/api/today`, lecciones de comienzo/medio/final de cada nivel, audio por HTTP, envío de tareas, repaso, grabación, transcripción y vuelta a abrir la app. Probar una copia de base con progreso previo y comprobar que las IDs siguen válidas. Verificar también en navegador las etiquetas de borrador, los huecos, carga sin conexión y compatibilidad de las funciones anteriores.
9. Pilotar con estudiantes reales y con evaluadores competentes: observar si pueden transferir lo aprendido a situaciones **nuevas** y cuánto tiempo útil emplean de verdad. Corregir secuencias demasiado fáciles/difíciles y sesgos de vocabulario. Mantener rúbricas y anotaciones de errores; separar autoevaluación, corrección automática limitada y evaluación humana.

### D. Empaquetar y comunicar honestamente

10. `./scripts/package-mac.sh` regenera JSON, prueba/audita y compila `dist/idiomas` para macOS arm64; **no genera automáticamente audio faltante**. Con la app cerrada o controlando solo el proceso propio, iniciar el nuevo binario. El código y los activos están incrustados: reiniciar el proceso anterior es necesario para servir el nuevo contenido. Comprobar el endpoint instalado en `8787` después, sin tocar la base real. No matar otros servicios ni procesos no identificados.
11. Actualizar README, el estado en pantalla y **este documento** con cifras obtenidas de la auditoría. Decir qué bloque se añadió, qué sigue siendo borrador, cuáles son los límites de evaluación y cuántas semanas faltan. No llamar «publicado», «validado» o «C2 alcanzado» a una lección generada que aún no pasó las puertas correspondientes.

## 7. Puertas de calidad y criterio de entrega final

Una semana solo pasa de **sin material → borrador** si tiene una fuente editable, una situación propia, lectura/escucha/escritura/producción pertinentes, respuestas y traducciones coherentes, audio accesible sin conexión, cinco lecciones utilizables y pruebas de integridad. Solo pasa de **borrador → revisado** tras corrección documentada por hablantes competentes y chequeo pedagógico. Un **nivel evaluado** exige pruebas independientes con material no visto y rúbricas; completar un repaso guiado no lo acredita. El **curso completo** exige las 200 semanas **por cada idioma**, cobertura de las destrezas y ruta profesional, continuidad y preservación de datos, audio, pruebas de uso real y transparencia editorial. Si faltan examinadores o estudiantes, dejar constancia de la dependencia; no simular su aprobación.

Lista final verificable:

- [x] Semanas **1–200 sin huecos ni duplicados**, por separado en `lb` y `da`, con 1.000 lecciones cada uno (verificado por `audit-course.py` y `tests/test_upper_expansion.py`). *La progresión A1–C2 está estructurada, pero su calidad pedagógica real sigue sin validar.*
- [x] **31 B1 + 31 B2 + 37 C1 + 37 C2** semanas nuevas **por idioma** redactadas como borradores. *Pendiente:* revisar esas 136 semanas y los 34 borradores previos por idioma con hablantes competentes.
- [~] Materiales de lectura, interacción y escritura originales para las 200 semanas; **audio a medio generar** (completar con `generate-audio.py --upper-expansion --missing lb da`). Traducción correcta y revisión competente **aún sin documentar**.
- [ ] Ruta laboral común y variantes de sector elegibles, con desempeño observable, no solo títulos profesionales.
- [ ] Evaluaciones iniciales, formativas y finales con situaciones no vistas y revisión humana para las destrezas abiertas; no confundir pruebas internas con certificación externa.
- [ ] Auditoría sin errores y avisos editoriales resueltos o justificados; tests de continuidad, API, navegador, audio/texto, accesibilidad, offline y regresión con base previa.
- [ ] Datos de progreso y grabaciones intactos tras actualizar; identificación estable de tarjetas y lecciones.
- [ ] Tiempo **real** de estudio registrado y estimaciones transparentes; no atribuir 1.000 horas por haber generado 1.000 fichas de lección.
- [ ] App instalada y comprobada en `8787`, documentación y UI alineadas con el estado verdadero; límites de validación claramente visibles.

**Prioridad inmediata:** la estructura de 200 semanas por idioma ya está cubierta con borradores originales. Los siguientes pasos, por orden, son: (1) **terminar la síntesis de audio** interrumpida (`generate-audio.py --upper-expansion --missing lb da`) para que la auditoría quede sin errores; (2) **revisión por hablantes competentes** de las 170 semanas en borrador por idioma, corrigiendo en `scripts/build-upper-expansion.py` y las fuentes A1/A2, con registro de nombre y fecha; (3) **pilotaje con estudiantes y evaluación con material no visto** para las destrezas abiertas. No hay atajo técnico que convierta automáticamente un temario de 200 semanas en competencia profesional: lo que se ha completado es la estructura y el contenido base, no la validación lingüística ni la acreditación de nivel.
