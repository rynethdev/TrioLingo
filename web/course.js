import {el, button, api, setStatus, statusNode} from './ui.js';
import {startRecorder} from './audio.js';

const levelNames = {A1: 'Principiante', A2: 'Básico', B1: 'Intermedio', B2: 'Intermedio alto', C1: 'Avanzado', C2: 'Maestría'};
const languageNames = {lb: 'luxemburgués', da: 'danés', fr: 'francés'};

function intro(title, subtitle, picker) {
  return el('div', {class: 'intro'}, el('div', {}, el('h1', {}, title), subtitle && el('p', {class: 'muted'}, subtitle)), picker);
}

function stat(value, label, detail) {
  return el('div', {class: 'stat-card'},
    el('strong', {}, String(value)),
    el('span', {}, label),
    detail && el('small', {}, detail));
}

// One shared player for the course: our own play buttons instead of native
// <audio controls>, which some Chromium browsers render as an empty box and
// which give no hint of what each bar is for.
const player = new Audio();
let playing = null;

function stopAudio() {
  player.pause();
  player.onended = null;
  if (playing) { const current = playing; playing = null; current.reset(); }
}

function playQueue(sources, node, idle) {
  if (playing?.node === node) { stopAudio(); return; }
  stopAudio();
  let position = 0;
  playing = {node, reset: () => { node.textContent = idle; node.classList.remove('playing'); }};
  node.textContent = '■ Parar';
  node.classList.add('playing');
  const step = () => {
    if (playing?.node !== node) return;
    if (position >= sources.length) { stopAudio(); return; }
    player.src = sources[position++];
    player.onended = () => setTimeout(step, 400);
    player.play().catch(() => { stopAudio(); node.textContent = 'Audio no disponible'; });
  };
  step();
}

// `label` is what the button says; `name` is the longer accessible name.
function listen(sources, label = 'Escuchar', name = label) {
  const idle = '▶ ' + label;
  const node = el('button', {type: 'button', class: 'button listen', 'aria-label': name}, idle);
  node.addEventListener('click', () => playQueue(sources, node, idle));
  return node;
}

function audio(src, name) {
  return listen([src], 'Escuchar', name);
}

function conversation(lines) {
  const sources = (lines || []).map(entry => entry.audio).filter(Boolean);
  return sources.length ? listen(sources, 'Escuchar la conversación') : null;
}

function progressBar(value, max, label) {
  return el('div', {class: 'progress-line'},
    el('progress', {max: Math.max(1, max), value, 'aria-label': label}),
    el('span', {class: 'muted'}, value + ' / ' + max));
}

function taskHeader(task, index, total) {
  const labels = {
    dialogue: 'Escucha', choice: 'Elige', reading: 'Lee', dictation: 'Dictado', translation: 'Traduce',
    cloze: 'Completa', speaking: 'Habla', pronunciation: 'Pronunciación', writing: 'Escribe',
    grammar: 'Gramática', review: 'Repaso',
  };
  return el('div', {class: 'task-head'},
    el('span', {class: 'kicker'}, (labels[task.kind] || task.kind) + ' · tarea ' + (index + 1) + ' de ' + total),
    el('h2', {}, task.prompt));
}

function feedbackNode(feedback) {
  if (!feedback) return el('div', {class: 'feedback', hidden: true});
  const heading = {correct: 'Correcto', correction: 'Casi', retry: 'Prueba otra vez', reference: 'Compara con el modelo'}[feedback.status] || 'Listo';
  return el('div', {class: 'feedback ' + feedback.status},
    el('strong', {}, heading),
    feedback.example && el('p', {lang: ''}, feedback.example),
    feedback.explanation && el('p', {}, feedback.explanation));
}

function lessonSummary(data, score, total, done) {
  const lesson = data.lesson;
  return el('div', {class: 'course'},
    intro('Lección terminada', lesson.title + ' · ' + lesson.level + ' · semana ' + lesson.week),
    el('section', {class: 'panel'},
      el('h2', {}, done ? 'Buen trabajo' : 'Sigue practicando'),
      el('p', {}, done
        ? 'Has completado las ' + total + ' tareas. Las palabras de esta lección entran hoy en tu repaso espaciado.'
        : 'Has hecho ' + score + ' de ' + total + ' tareas. Puedes volver mañana o repetir la lección ahora.'),
      progressBar(score, total, 'Tareas completadas'),
      el('div', {class: 'row'},
        button('Volver a Hoy', () => { location.hash = '#hoy'; }, true),
        button('Repasar vocabulario', () => { location.hash = '#vocabulario'; }),
        button('Ver el curso', () => { location.hash = '#curso'; }))));
}

export function todayView({lang, picker}) {
  const root = el('div', {class: 'course'});
  root.append(intro('Hoy', 'Una sesión corta, cinco días por semana, un camino largo y visible.', picker));
  const body = el('div', {}, el('p', {class: 'status'}, 'Cargando tu plan…'));
  root.append(body);
  api('today?lang=' + lang).then(data => {
    const stats = data.stats;
    const next = data.next;
    const due = data.due;
    const hero = el('section', {class: 'session-hero'},
      el('div', {},
        el('span', {class: 'kicker'}, 'Semana ' + stats.week + ' de ' + stats.total_weeks + ' · ' + stats.level + ' · ' + (levelNames[stats.level] || '')),
        el('h2', {}, next ? next.title : 'Bloque terminado'),
        el('p', {}, next ? next.goal : data.next_available
          ? 'Faltan semanas de contenido entre este bloque y la semana ' + data.next_available.week + '. Puedes explorarla en Curso, pero no equivale a haber superado las semanas intermedias.'
          : 'Has terminado las lecciones disponibles. Sigue repasando: completar tareas no acredita un nivel MCER.'),
        data.unit?.editorial_status && el('p', {class: 'muted'}, 'Borrador: ' + data.unit.editorial_status + '. Úsalo como práctica, no como referencia definitiva.'),
        el('div', {class: 'row'},
          next && button('Empezar la sesión de hoy', () => { location.hash = '#leccion/' + next.id; }, true),
          !next && data.next_available && el('a', {class: 'button', href: '#curso'}, 'Explorar otros bloques'),
          due.count > 0 && el('a', {class: 'button', href: '#vocabulario'}, 'Repasar ' + due.count + ' tarjetas'))),
      el('div', {class: 'hero-meter'},
        el('strong', {}, stats.lessons_completed + ' / ' + stats.lessons_total),
        el('span', {}, 'lecciones disponibles'),
        progressBar(stats.lessons_completed, stats.lessons_total, 'Lecciones completadas'),
        el('small', {}, 'Objetivo ' + stats.level + ': ' + stats.hours_low + '–' + stats.hours_high + ' h')));

    const statsGrid = el('section', {class: 'stat-grid'},
      stat(stats.streak, 'días seguidos', 'Racha actual'),
      stat(stats.minutes_week, 'minutos esta semana', 'medidos en lecciones'),
      stat(stats.tasks_done, 'tareas hechas', 'Desde el inicio'),
      stat(stats.vocabulary.learned + ' / ' + stats.vocabulary.total, 'expresiones repasadas', stats.vocabulary.due + ' vencen hoy'));

    const plan = data.unit ? el('section', {class: 'panel week-plan'},
      el('div', {class: 'section-head'},
        el('div', {}, el('h2', {}, 'Semana ' + data.unit.week + ' · ' + data.unit.title),
          el('p', {class: 'muted'}, 'Puedo: ' + data.unit.can_do))),
      el('ol', {}, data.unit.lessons.map(lesson => el('li', {class: lesson.completed ? 'done' : ''},
        el('span', {class: 'day'}, 'Día ' + lesson.day),
        el('div', {}, el('strong', {}, lesson.title),
          el('small', {}, lesson.completed ? 'Completada' : lesson.tasks_done + ' de ' + lesson.tasks_total + ' tareas')),
        el('a', {class: 'button', href: '#leccion/' + lesson.id}, lesson.completed ? 'Repetir' : lesson.tasks_done ? 'Continuar' : 'Abrir'))))) : null;

    const duePanel = due.count ? el('section', {class: 'panel'},
      el('div', {class: 'section-head'},
        el('div', {}, el('h2', {}, 'Repaso de hoy'),
          el('p', {class: 'muted'}, 'Estas palabras vencen hoy. Recuperarlas ahora es lo que las fija.')),
        el('a', {class: 'button primary', href: '#vocabulario'}, 'Empezar repaso')),
      el('div', {class: 'chip-row'}, due.items.slice(0, 12).map(item =>
        el('span', {class: 'word-chip'}, item.text, el('small', {}, item.translation))))) : null;

    const method = el('details', {class: 'panel review-later'},
      el('summary', {}, 'Cómo funciona el curso'),
      el('ol', {},
        el('li', {}, 'Cada unidad tiene cinco lecciones: escuchar, vocabulario, gramática, hablar y cerrar con lectura y escritura. Repite y amplía la práctica hasta tu meta semanal.'),
        el('li', {}, 'Las expresiones de cada lección entran en el repaso espaciado al completarla. La frecuencia depende de cómo califiques cada tarjeta.'),
        el('li', {}, 'El objetivo es llegar a C2 en unas 200 semanas. No hay prisa: lo importante es no saltarse el repaso.'),
        el('li', {}, 'A1 y A2 son la base. Desde B1 aparecen situaciones laborales; el trabajo especializado por sector sigue pendiente.')));

    body.replaceChildren(...[hero, statsGrid, duePanel, plan, method].filter(Boolean));
  }).catch(error => { body.textContent = error.message; });
  return root;
}

export function courseView({lang, picker}) {
  const root = el('div', {class: 'course'});
  root.append(intro('Curso', 'A1 y A2 continuos, con borradores pendientes de revisión. Los niveles posteriores siguen por bloques.', picker));
  const body = el('div', {}, el('p', {class: 'status'}, 'Cargando el curso…'));
  root.append(body);
  api('course?lang=' + lang).then(data => {
    const groups = new Map();
    for (const unit of data.units) {
      if (!groups.has(unit.level)) groups.set(unit.level, []);
      groups.get(unit.level).push(unit);
    }
    const available = new Set(groups.keys());
    const coverage = new Map((data.coverage || []).map(entry => [entry.level, entry]));
    const sections = [...groups.entries()].map(([level, units]) => el('section', {class: 'panel course-level'},
      el('div', {class: 'section-head'},
        el('div', {}, el('h2', {}, level + ' · ' + (levelNames[level] || '')),
          el('p', {class: 'muted'}, units.length + ' unidades con material')),
        el('span', {class: 'level'}, level)),
      units.map(unit => el('div', {class: 'unit-block'},
        el('div', {class: 'unit-head'},
          el('div', {}, el('h3', {}, 'Semana ' + unit.week + ' · ' + unit.title),
            el('p', {class: 'muted'}, 'Puedo: ' + unit.can_do),
            unit.editorial_status && el('p', {class: 'muted'}, 'Borrador · ' + unit.editorial_status))),
        el('div', {class: 'lesson-row'}, unit.lessons.map(lesson =>
          el('a', {class: 'lesson-chip' + (lesson.completed ? ' done' : ''), href: '#leccion/' + lesson.id},
            el('span', {class: 'day'}, 'D' + lesson.day),
            el('strong', {}, lesson.title),
            el('small', {}, lesson.completed ? 'Completada' : lesson.tasks_done + '/' + lesson.tasks_total))))))));
    const note = el('section', {class: 'panel'},
      el('h2', {}, 'El camino completo'),
      el('p', {}, 'Hay ' + data.units.length + ' unidades y ' + data.stats.lessons_total + ' lecciones disponibles para este idioma. El plan completo exige 200 unidades, 1.000 lecciones y unas 1.000 horas de práctica real por idioma.'),
      el('p', {}, 'Faltan ' + Math.max(0, 200 - data.units.length) + ' semanas con material nuevo para este idioma.'),
      el('p', {class: 'muted'}, 'El mapa indica una meta de estudio, no 200 semanas de contenido ya publicado: A1: 20 · A2: 24 · B1: 36 · B2: 36 · C1: 42 · C2: 42.'));
    const roadmap = data.roadmap ? el('section', {class: 'panel'},
      el('h2', {}, 'Mapa del curso · 200 semanas'),
      el('p', {class: 'muted'}, 'A1 semanas 6–20 y A2 semanas intermedias: borradores sin revisión externa. B1–C2: solo bloques iniciales. Ver el mapa no equivale a haber estudiado las semanas ausentes.'),
      el('div', {class: 'roadmap'}, data.roadmap.map(stage => el('div', {class: 'roadmap-stage' + (available.has(stage.level) ? ' active' : '')},
        el('span', {class: 'level'}, stage.level),
        el('div', {}, el('strong', {}, stage.title),
          el('small', {}, 'Semanas ' + stage.start + '–' + stage.end + ' · meta ' + stage.hours + ' h'),
          coverage.get(stage.level) && el('small', {}, 'Con material: ' + coverage.get(stage.level).published_weeks.join(', ') + ' (' + coverage.get(stage.level).published_weeks.length + ' de ' + coverage.get(stage.level).planned_weeks + ' semanas; revisa los borradores)'),
          el('p', {}, stage.focus)),
        el('span', {class: 'caption'}, coverage.get(stage.level)?.draft_weeks?.length
          ? coverage.get(stage.level).draft_weeks.length + ' borradores sin revisar'
          : available.has(stage.level) ? 'Bloque inicial' : 'Próximamente'))))) : null;
    body.replaceChildren(...[sections, note, roadmap].flat().filter(Boolean));
  }).catch(error => { body.textContent = error.message; });
  return root;
}

export function lessonView(id, {lang} = {}) {
  const root = el('div', {class: 'course lesson-view'});
  const body = el('div', {}, el('p', {class: 'status'}, 'Cargando la lección…'));
  root.append(body);
  let dispose = () => {};
  root.addEventListener('DOMNodeRemoved', () => dispose());

  api('lesson/' + id).then(data => {
    const lesson = data.lesson;
    const tasks = lesson.tasks;
    const itemsById = new Map((data.items || []).map(item => [item.id, item]));
    const doneTasks = new Set(data.done_tasks || []);
    let index = 0;
    while (index < tasks.length && doneTasks.has(index)) index += 1;
    let score = doneTasks.size;
    let attempts = doneTasks.size;
    let activeTask = null;
    let furthest = index;  // lets the learner go back and forward over seen tasks

    const progress = el('div', {class: 'lesson-progress'});
    const stage = el('div', {});
    const top = el('div', {class: 'lesson-top'},
      el('a', {class: 'text-link', href: '#hoy'}, '← Volver a Hoy'),
      el('div', {}, el('strong', {}, lesson.title),
        el('small', {}, lesson.level + ' · semana ' + lesson.week + ' · día ' + lesson.day),
        data.unit?.editorial_status && el('small', {}, 'Borrador: ' + data.unit.editorial_status)));
    root.replaceChildren(top, progress, stage);

    function draw() {
      activeTask?.cleanup();
      stopAudio();
      if (index >= tasks.length) {
        stage.replaceChildren(lessonSummary(data, score, tasks.length, score === tasks.length));
        progress.replaceChildren();
        return;
      }
      const go = target => { index = target; draw(); window.scrollTo({top: 0, behavior: 'smooth'}); };
      progress.replaceChildren(progressBar(index, tasks.length, 'Progreso de la lección'),
        el('div', {class: 'row lesson-nav'},
          index > 0 && button('← Anterior', () => go(index - 1)),
          index < furthest && button('Siguiente →', () => go(index + 1))));
      const task = tasks[index];
      const next = () => { furthest = Math.max(furthest, index + 1); go(index + 1); };
      const complete = () => {
        // Redoing a task after going back must not count it twice.
        if (!doneTasks.has(index)) score += 1;
        doneTasks.add(index);
        attempts += 1;
        next();
      };
      activeTask = renderTask(task, index, tasks.length, {lang: lesson.lang, lessonId: lesson.id, itemsById, onDone: complete, next, setScore: () => { score += 1; }});
      stage.replaceChildren(activeTask);
    }
    draw();
    dispose = () => { activeTask?.cleanup(); stopAudio(); };
  }).catch(error => { body.textContent = error.message; });
  return root;
}

function renderTask(task, index, total, context) {
  const card = el('section', {class: 'panel task-card'});
  card.append(taskHeader(task, index, total));
  const feedback = el('div', {});
  const controls = el('div', {class: 'row task-actions'});
  const status = statusNode();
  let done = false;
  let check = null;
  let activeMs = 0;
  let lastActive = document.visibilityState === 'visible' ? performance.now() : null;
  const visible = () => {
    if (lastActive !== null) activeMs += performance.now() - lastActive;
    lastActive = document.visibilityState === 'visible' ? performance.now() : null;
  };
  document.addEventListener('visibilitychange', visible);
  card.cleanup = () => document.removeEventListener('visibilitychange', visible);
  const elapsed = () => {
    visible();
    const seconds = Math.min(600, Math.floor(activeMs / 1000));
    activeMs = 0;
    return seconds;
  };

  const finish = async () => {
    if (done) return;
    done = true;
    if (!['choice', 'reading', 'cloze', 'dictation', 'translation', 'speaking', 'writing'].includes(task.kind)) {
      try {
        await api('lesson/answer', {id: crypto.randomUUID(), lesson: context.lessonId, task: index, duration_seconds: elapsed()});
      } catch (error) {
        setStatus(status, error.message, true);
      }
    }
    document.removeEventListener('visibilitychange', visible);
    context.onDone();
  };
  const skip = () => {
    if (done) return;
    done = true;
    document.removeEventListener('visibilitychange', visible);
    context.next();
  };

  async function send(body) {
    try {
      const result = await api('lesson/answer', {id: crypto.randomUUID(), lesson: context.lessonId, task: index, duration_seconds: elapsed(), ...body});
      feedback.replaceChildren(feedbackNode(result.feedback));
      return result;
    } catch (error) {
      setStatus(status, error.message, true);
      return null;
    }
  }

  function after(result) {
    if (!result) return;
    if (result.graded && !result.correct) {
      if (check) { check.disabled = false; check.hidden = false; }
      if (!card.querySelector('.skip')) {
        controls.append(el('button', {type: 'button', class: 'button skip', onclick: skip}, 'Saltar por ahora'));
      }
      setStatus(status, 'Todavía no. Revisa el modelo e inténtalo otra vez.');
      return;
    }
    setStatus(status, result.graded ? 'Correcto.' : 'Tarea completada.');
    controls.replaceChildren(button(index + 1 >= total ? 'Terminar lección' : 'Siguiente', finish, true));
  }

  function wireCheck(input, buildBody) {
    check = button('Comprobar', async () => {
      if (input && !input.value.trim()) {
        setStatus(status, 'Escribe una respuesta antes de comprobar.', true);
        return;
      }
      const body = buildBody ? buildBody() : {text: input.value};
      if (!body) {
        setStatus(status, 'Elige una opción antes de comprobar.', true);
        return;
      }
      check.disabled = true;
      const result = await send(body);
      after(result);
      if (!result) check.disabled = false;
    }, true);
    controls.append(check);
    if (input) {
      input.addEventListener('keydown', event => {
        if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); check.click(); }
      });
    }
  }

  switch (task.kind) {
    case 'dialogue': {
      const lines = task.lines || [];
      const all = conversation(lines);
      if (all) card.append(el('div', {class: 'listen-block'}, all,
        el('small', {class: 'muted'}, 'Escúchala entera o frase por frase con el botón de cada línea.')));
      card.append(el('div', {class: 'dialogue-list'}, lines.map(entry =>
        el('div', {class: 'audio-line' + (entry.speaker === 1 ? ' mine' : '')},
          el('div', {}, el('span', {lang: context.lang}, entry.text), el('small', {}, entry.es)),
          entry.audio && audio(entry.audio, 'Escuchar: ' + entry.text)))));
      controls.append(button('Hecho, continuar', finish, true));
      card.append(controls);
      break;
    }
    case 'choice':
    case 'reading': {
      if (task.audio) card.append(audio(task.audio, 'Escuchar la lectura'));
      // Listening questions carry the dialogue audio in `lines`: play it
      // without the text, so the answer still has to come from listening.
      const all = conversation(task.lines);
      if (all) card.append(el('div', {class: 'listen-block'}, all,
        el('small', {class: 'muted'}, 'Escucha la conversación (las veces que quieras) y elige la respuesta.')));
      if (task.text) card.append(el('blockquote', {class: 'reading-text', lang: context.lang}, task.text));
      const form = el('form', {class: 'choice-list'}, (task.choices || []).map((choice, order) =>
        el('label', {class: 'choice'}, el('input', {type: 'radio', name: 'choice-' + index, value: String(order)}), choice)));
      wireCheck(null, () => {
        const picked = new FormData(form).get('choice-' + index);
        return picked === null ? null : {choice: Number(picked)};
      });
      card.append(form, controls, status, feedback);
      break;
    }
    case 'cloze':
    case 'dictation':
    case 'translation': {
      if (task.audio) card.append(audio(task.audio, 'Escucha el dictado'));
      const input = el('textarea', {lang: context.lang, rows: '2', spellcheck: 'false', placeholder: 'Escribe la respuesta…'});
      wireCheck(input);
      card.append(input, controls, status, feedback);
      break;
    }
    case 'speaking': {
      if (task.es) card.append(el('p', {class: 'muted'}, task.es));
      if (task.audio) card.append(audio(task.audio, 'Escucha la pregunta'));
      if (task.model_audio) card.append(audio(task.model_audio, 'Escucha el modelo'));
      if (task.model) card.append(el('details', {}, el('summary', {}, 'Ver el modelo'), el('p', {lang: context.lang}, task.model)));
      if (task.tip) card.append(el('p', {class: 'muted'}, task.tip));
      const input = el('textarea', {lang: context.lang, rows: '3', spellcheck: 'false', placeholder: 'Escribe lo que dirías o transcribe tu grabación…'});
      const comparison = el('audio', {controls: true, 'aria-label': 'Tu grabación'});
      const recordStatus = statusNode();
      const recorder = startRecorder(recordStatus, input, comparison, context.lang, false, () => {}, () => {});
      card.append(input, el('div', {class: 'row'}, recorder.control), comparison, recordStatus);
      wireCheck(input);
      card.append(controls, status, feedback);
      break;
    }
    case 'pronunciation': {
      card.append(el('p', {class: 'muted'}, task.tip || 'Escucha, repite y compara.'));
      const lines = task.lines || [];
      card.append(el('div', {class: 'dialogue-list'}, lines.map(entry =>
        el('div', {class: 'audio-line'},
          el('div', {}, el('span', {lang: context.lang}, entry.text), entry.es && el('small', {}, entry.es)),
          entry.audio && audio(entry.audio, 'Escuchar ' + entry.text)))));
      controls.append(button('Hecho, continuar', finish, true));
      card.append(controls);
      break;
    }
    case 'writing': {
      const input = el('textarea', {lang: context.lang, rows: '5', spellcheck: 'false', placeholder: 'Escribe tu texto…'});
      check = button('Enviar y comparar', async () => {
        if (!input.value.trim()) { setStatus(status, 'Escribe algo antes de enviar.', true); return; }
        check.disabled = true;
        const result = await send({text: input.value});
        after(result);
        if (!result) check.disabled = false;
      }, true);
      controls.append(check);
      card.append(input, controls, status, feedback);
      if (task.rubric) card.append(el('p', {class: 'muted'}, 'Criterios: ' + task.rubric));
      break;
    }
    case 'grammar': {
      card.append(el('div', {class: 'grammar-note'}, el('p', {}, task.text || '')));
      const examples = task.lines || [];
      if (examples.length) card.append(el('div', {class: 'dialogue-list'}, examples.map(entry =>
        el('div', {class: 'audio-line'}, el('div', {}, el('span', {lang: context.lang}, entry.text), entry.es && el('small', {}, entry.es))))));
      controls.append(button('Entendido', finish, true));
      card.append(controls);
      break;
    }
    case 'review': {
      const ids = task.items || [];
      card.append(el('p', {class: 'muted'}, 'Estas expresiones entran en el repaso espaciado al completar la lección.'));
      card.append(el('div', {class: 'chip-row'}, ids.map(id => {
        const item = context.itemsById.get(id);
        return item && el('span', {class: 'word-chip'}, item.text, el('small', {}, item.translation));
      }).filter(Boolean)));
      controls.append(button('Hecho, continuar', finish, true));
      card.append(controls);
      break;
    }
    default: {
      controls.append(button('Hecho, continuar', finish, true));
      card.append(controls);
    }
  }
  return card;
}

export function vocabView({lang, picker}) {
  const root = el('div', {class: 'course'});
  root.append(intro('Vocabulario', 'Repaso espaciado: cada palabra vuelve justo antes de que se te olvide.', picker));
  const body = el('div', {}, el('p', {class: 'status'}, 'Cargando tus tarjetas…'));
  root.append(body);

  function load() {
    api('srs/due?lang=' + lang + '&limit=40').then(data => {
      const items = data.items;
      const stats = data.stats;
      if (!items.length) {
        body.replaceChildren(el('section', {class: 'panel'},
          el('h2', {}, 'Repaso al día'),
          el('p', {}, 'No tienes tarjetas vencidas. Vuelve mañana o abre la lección de hoy para añadir palabras nuevas.'),
          el('div', {class: 'row'},
            el('a', {class: 'button primary', href: '#hoy'}, 'Ir a la sesión de hoy'),
            el('a', {class: 'button', href: '#curso'}, 'Ver el curso')),
          el('div', {class: 'stat-grid'},
            stat(stats.learned, 'expresiones repasadas', 'de ' + stats.total + ' introducidas'),
            stat(stats.reviews_today, 'repasos hoy', stats.reviews_week + ' esta semana'))));
        return;
      }
      let position = 0;
      let reviewed = 0;
      const stage = el('div', {});
      const counter = el('p', {class: 'muted'});
      body.replaceChildren(el('div', {class: 'stat-grid'},
        stat(stats.due, 'vencen hoy', 'de ' + stats.total + ' palabras'),
        stat(stats.learned, 'repasadas', 'con al menos un repaso'),
        stat(stats.reviews_today, 'repasos hoy', stats.reviews_week + ' esta semana')), stage);

      function draw() {
        if (position >= items.length) {
          stage.replaceChildren(el('section', {class: 'panel'},
            el('h2', {}, 'Repaso terminado'),
            el('p', {}, 'Has repasado ' + reviewed + ' tarjetas. Las que has recordado volverán más tarde; las difíciles, mañana.'),
            el('div', {class: 'row'},
              button('Repasar más', load, true),
              el('a', {class: 'button', href: '#hoy'}, 'Volver a Hoy'))));
          return;
        }
        const item = items[position];
        counter.textContent = (position + 1) + ' de ' + items.length;
        const answer = el('div', {class: 'flash-answer', hidden: true},
          el('p', {}, item.translation),
          item.example && el('p', {lang: lang}, item.example),
          item.example_es && el('p', {class: 'muted'}, item.example_es),
          item.audio && audio(item.audio, 'Escuchar ' + item.text));
        const grades = el('div', {class: 'grade-row', hidden: true},
          button('Otra vez', () => grade(0), false),
          button('Difícil', () => grade(1), false),
          button('Bien', () => grade(2), true),
          button('Fácil', () => grade(3), false));
        const reveal = button('Mostrar respuesta', () => {
          answer.hidden = false;
          grades.hidden = false;
          reveal.hidden = true;
        }, true);
        stage.replaceChildren(el('section', {class: 'panel flashcard'},
          counter,
          el('span', {class: 'kicker'}, item.level + ' · ' + (item.reps ? 'repasada ' + item.reps + ' veces' : 'nueva')),
          el('h2', {lang: lang}, item.text),
          reveal, answer, grades));
      }

      async function grade(value) {
        const item = items[position];
        for (const control of grades.querySelectorAll('button')) control.disabled = true;
        try {
          await api('srs/review', {id: crypto.randomUUID(), item: item.id, grade: value});
          reviewed += 1;
          position += 1;
          draw();
        } catch (error) {
          for (const control of grades.querySelectorAll('button')) control.disabled = false;
          stage.append(el('p', {class: 'status error'}, error.message));
        }
      }
      draw();
    }).catch(error => { body.textContent = error.message; });
  }
  load();
  return root;
}

export function progressView({lang, picker}) {
  const root = el('div', {class: 'course'});
  root.append(intro('Progreso', 'Lo que se mide, se puede mejorar. Aquí ves el camino completo.', picker));
  const body = el('div', {}, el('p', {class: 'status'}, 'Cargando tu progreso…'));
  root.append(body);
  api('learning/summary?lang=' + lang).then(data => {
    const vocab = data.vocabulary;
    const byLevel = el('div', {class: 'level-progress'}, data.by_level.map(level =>
      el('div', {class: 'level-row'},
        el('div', {class: 'level-label'}, el('strong', {}, level.level), el('span', {}, level.done + ' / ' + level.total)),
        progressBar(level.done, level.total, 'Progreso ' + level.level))));
    body.replaceChildren(
      el('section', {class: 'stat-grid'},
        stat(data.level, 'último bloque practicado', 'no es una certificación'),
        stat(data.lessons_completed + ' / ' + data.lessons_total, 'lecciones', 'con material'),
        stat(data.tasks_done, 'tareas completadas', 'desde el inicio'),
        stat(data.streak, 'días seguidos', 'racha actual')),
      el('section', {class: 'panel'},
        el('h2', {}, 'Tiempo y práctica'),
        progressBar(data.lessons_completed, data.lessons_total, 'Lecciones publicadas'),
        el('p', {class: 'muted'}, 'Tiempo medido en lecciones desde esta actualización: ' + data.hours_measured + ' h. No incluye práctica fuera de la app ni acredita un nivel. La referencia para ' + data.level + ' es de ' + data.hours_low + ' a ' + data.hours_high + ' horas acumuladas.'),
        el('p', {class: 'muted'}, 'El curso completo son 200 semanas y unas 1.000 horas. La constancia semanal importa más que la velocidad.')),
      el('section', {class: 'panel'},
        el('h2', {}, 'Vocabulario'),
        el('div', {class: 'stat-grid'},
          stat(vocab.learned, 'repasadas', 'con al menos un repaso'),
          stat(vocab.due, 'vencen hoy', 'pendientes'),
          stat(vocab.reviews_week, 'repasos esta semana', vocab.reviews_today + ' hoy'),
          stat(vocab.total, 'introducidas', 'en el curso')),
        el('p', {class: 'muted'}, 'Una tarjeta repasada no equivale a una palabra dominada. La cobertura léxica y la comprensión se deben comprobar con textos y conversaciones nuevas.')),
      el('section', {class: 'panel'},
        el('h2', {}, 'Por nivel'),
        byLevel),
      el('section', {class: 'panel'},
        el('h2', {}, 'Qué hacer ahora'),
        el('div', {class: 'row'},
          el('a', {class: 'button primary', href: '#hoy'}, 'Sesión de hoy'),
          el('a', {class: 'button', href: '#vocabulario'}, 'Repasar vocabulario'),
          el('a', {class: 'button', href: '#curso'}, 'Ver el curso'))));
  }).catch(error => { body.textContent = error.message; });
  return root;
}
