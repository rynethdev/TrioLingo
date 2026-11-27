import {startRecorder} from './audio.js';
import {fieldView, loadField} from './field.js';
import {el, button, api, setStatus, statusNode, audioPath} from './ui.js';
import {levels, activitiesFor, reportView, journalView, assessmentView, wordsView} from './study.js';
import {todayView, courseView, lessonView, vocabView, progressView as courseProgressView} from './course.js';

const app = document.querySelector('#app');
const languages = {lb: ['🇱🇺', 'Luxemburgués', 'Lëtzebuergesch'], da: ['🇩🇰', 'Danés', 'Dansk'], fr: ['🇱🇺', 'Francés', 'Français']};
const sections = [
  ['listening', 'Escucha'], ['talk', 'Conversación'], ['reading', 'Lectura'], ['writing', 'Escritura'], ['drills', 'Ejercicios'],
];
const state = {
  lang: Object.hasOwn(languages, localStorage.getItem('idiomas.lang')) ? localStorage.getItem('idiomas.lang') : 'lb',
  cloud: localStorage.getItem('idiomas.cloud') === 'true',
  section: 'listening', turn: 0, drill: 0, scene: null,
  catalog: null, progress: null, dispose: () => {},
};

function completed(sceneId, activity) {
  return state.progress.activities.some(value => value.scene === sceneId && value.activity === activity);
}

function completedCount(scene) {
  return activitiesFor(scene).filter(activity => completed(scene.id, activity)).length;
}

async function refreshProgress() {
  state.progress = await api('progress');
  const count = [...state.progress.reviews, ...state.progress.exercises].filter(item => item.due).length;
  const badge = document.querySelector('#due-count');
  badge.textContent = count;
  badge.hidden = count === 0;
}

async function submit(scene, activity, values, id) {
  const feedback = await api('attempts', {id, scene: scene.id, activity, ...values});
  await refreshProgress().catch(() => {});
  return feedback;
}

function setLanguage(value) {
  state.lang = value;
  localStorage.setItem('idiomas.lang', value);
}

function goToScene(scene) {
  location.hash = '#escena/' + scene.id;
}

function activeLevel() {
  const stored = localStorage.getItem('idiomas.level.' + state.lang);
  return routeLevels().includes(stored) ? stored : 'A1';
}

function routeLevels() {
  return levels.filter(level => state.catalog.scenes.some(scene => scene.lang === state.lang && scene.level === level));
}

function setLevel(level) {
  localStorage.setItem('idiomas.level.' + state.lang, level);
}

function languagePicker() {
  return el('div', {class: 'lang-switch', role: 'group', 'aria-label': 'Idioma de práctica'},
    Object.entries(languages).map(([id, [flag, name]]) => el('button', {
      type: 'button', 'aria-pressed': id === state.lang ? 'true' : 'false',
      onclick: () => {
        setLanguage(id);
        render();
        app.querySelector('.lang-switch [aria-pressed=true]').focus();
      },
    }, el('span', {'aria-hidden': 'true'}, flag + ' '), name)));
}

function showHome() {
  const level = activeLevel();
  const lang = state.lang;
  const scenes = state.catalog.scenes.filter(scene => scene.lang === lang && scene.level === level);
  const next = scenes.find(scene => completedCount(scene) < activitiesFor(scene).length) || scenes[0];
  const totalDone = scenes.filter(scene => completedCount(scene) === activitiesFor(scene).length).length;
  const due = [...state.progress.reviews, ...state.progress.exercises].filter(item => item.due && item.scene.startsWith(lang + '-')).length;
  const waveform = el('div', {class: 'waveform', 'aria-hidden': 'true'},
    Array.from({length: 21}, () => el('i')));
  const cards = scenes.map(scene => {
    const count = completedCount(scene);
    const total = activitiesFor(scene).length;
    return el('button', {class: 'level-card' + (scene.checkpoint ? ' checkpoint-card' : ''), type: 'button', onclick: () => goToScene(scene)},
      el('span', {class: 'level'}, scene.checkpoint ? 'Control de nivel' : 'Semana ' + scene.week),
      el('h3', {}, scene.checkpoint ? scene.title.split(' · ').at(-1) : scene.title), el('p', {}, scene.goal),
      el('span', {class: 'caption'}, count === total ? 'Escena practicada' : count ? count + ' de ' + total + ' actividades' : 'Abrir escena'));
  });
  const today = el('p', {class: 'muted'}, due ? due + ' ejercicios te esperan en el repaso.' : 'Tu repaso está al día.');
  const suggestion = el('div', {class: 'row'});
  const tiles = el('section', {class: 'study-overview'},
    el('div', {}, el('h2', {}, 'En qué enfocarte hoy'), today,
      el('a', {class:'button primary', href:'#practica/hoy'}, 'Preparar mi sesión'), suggestion),
    el('div', {}, el('h3', {}, 'Avance en ' + level), el('progress', {max: scenes.length, value: totalDone, 'aria-label': 'Escenas practicadas'}),
      el('p', {class: 'muted'}, totalDone + ' de ' + scenes.length + ' escenas practicadas')));
  api('diagnostics/' + lang).then(report => {
    if (!suggestion.isConnected) return;
    const miss = report.measurements.find(item => item.last !== 'correct');
    if (!miss) return;
    suggestion.append(el('a', {class: 'text-link', href: '#progreso'}, 'Revisa tus errores recientes'));
  }).catch(() => {});
  app.append(el('div', {class: 'intro'},
    el('div', {}, el('h1', {}, 'Practica para tu mudanza'), el('p', {}, lang === 'fr' ? 'Francés práctico para vivir y trabajar en Luxemburgo.' : 'Treinta semanas de práctica por idioma, a tu ritmo.')), languagePicker()),
    el('nav', {class: 'level-picker', 'aria-label': 'Nivel de la ruta'},
      routeLevels().map(value => el('button', {type: 'button', 'aria-pressed': value === level ? 'true' : 'false',
        onclick: () => { setLevel(value); render(); app.querySelector('.level-picker [aria-pressed=true]').focus(); }}, value))),
    el('section', {class: 'hero', 'aria-labelledby': 'next-title'},
      el('div', {}, el('span', {class: 'kicker'}, (totalDone === scenes.length ? 'Volver a practicar' : 'Siguiente práctica') + ' · ' + next.level + ' · Semana ' + next.week),
        el('h2', {id: 'next-title'}, next.title), el('p', {}, next.setup),
        el('div', {class: 'row'}, button(completedCount(next) ? 'Continuar práctica' : 'Empezar práctica', () => goToScene(next), true),
          due > 0 && el('a', {class: 'button', href:'#repaso'}, 'Repasar pendientes'))), waveform),
    tiles, el('div', {class: 'section-head'}, el('div', {}, el('h2', {}, 'Tu ruta ' + level),
      el('p', {class: 'muted'}, 'Dedica una semana a cada escena.'))),
    el('section', {class: 'level-grid', 'aria-label': 'Escenas del nivel ' + level}, cards),
    el('details', {class:'panel review-later'},
      el('summary', {}, 'Cómo repartir la práctica durante la semana'),
      el('ol', {},
        el('li', {}, 'Escucha a velocidad normal y comprueba qué entendiste. Lee el texto y vuelve al audio en los puntos difíciles.'),
        el('li', {}, 'Practica el diálogo otro día. Grábate primero con la referencia y después por tu cuenta.'),
        el('li', {}, 'Escribe una respuesta propia, haz los ejercicios y visita Progreso para corregir un punto débil.'),
        el('li', {}, 'Haz el repaso cuando venza. Al terminar el nivel, resuelve la situación del control.'))));
}

function feedbackPanel(target, feedback, language) {
  const heading = {
    correct: 'Bien hecho', correction: 'Prueba este cambio', retry: 'Escucha o lee de nuevo', reference: 'Compara con este ejemplo',
  }[feedback.status];
  target.replaceChildren(el('div', {class: 'feedback ' + feedback.status},
    el('strong', {}, heading),
    feedback.status !== 'retry' && el('p', {lang: language}, feedback.example),
    feedback.explanation && el('p', {}, feedback.explanation)));
}

function quizView(scene, activity) {
  const quiz = scene[activity];
  const response = el('div', {role: 'status'});
  const field = el('fieldset', {}, el('legend', {}, quiz.prompt),
    quiz.choices.map((choice, index) => el('label', {class: 'choice'},
      el('input', {type: 'radio', name: 'choice', value: String(index), required: true}), choice)));
  const check = el('button', {class: 'button primary', type: 'submit'}, 'Comprobar');
  const next = button(activity === 'listening' ? 'Continuar a conversación' : 'Continuar a escritura', () => {
    state.section = activity === 'listening' ? 'talk' : 'writing';
    render(true);
  }, true);
  next.hidden = !completed(scene.id, activity);
  const form = el('form', {onsubmit: async event => {
    event.preventDefault();
    const value = new FormData(form).get('choice');
    if (value === null) return;
    field.disabled = check.disabled = true;
    try {
      const result = await submit(scene, activity, {choice: Number(value)}, crypto.randomUUID());
      feedbackPanel(response, result);
      if (result.status === 'correct') {
        check.textContent = 'Comprobar de nuevo';
        next.hidden = false;
      }
    } catch (error) {
      response.textContent = error.message;
    } finally {
      field.disabled = check.disabled = false;
    }
  }}, field, el('div', {class: 'row'}, check, next), response);
  return el('section', {class: 'panel'},
    activity === 'reading' && el('p', {class: 'prompt', lang: scene.lang}, quiz.text), form);
}

function listeningView(scene) {
  const player = el('audio', {controls: true, preload: 'none', 'aria-label': 'Audio de la escena'});
  const status = statusNode();
  let index = 0;
  let continuous = false;
  let slow = false;
  const speed = button('Velocidad lenta', () => {
    slow = !slow;
    speed.setAttribute('aria-pressed', String(slow));
    speed.textContent = slow ? 'Velocidad normal' : 'Velocidad lenta';
    player.playbackRate = slow ? 0.75 : 1;
    setStatus(status, slow ? 'Velocidad lenta activada.' : 'Velocidad normal activada.');
  });
  speed.setAttribute('aria-pressed', 'false');
  async function play(line, all = false) {
    index = line;
    continuous = all;
    player.src = audioPath(scene, 'line', index);
    player.playbackRate = slow ? 0.75 : 1;
    setStatus(status, 'Fragmento ' + (index + 1) + ' de ' + scene.dialogue.length);
    try { await player.play(); } catch { setStatus(status, 'Usa el control de audio para reproducir el fragmento.'); }
  }
  player.addEventListener('ended', () => {
    if (continuous && index + 1 < scene.dialogue.length) play(index + 1, true);
    else setStatus(status, 'Audio terminado.');
  });
  player.src = audioPath(scene, 'line', 0);
  state.dispose = () => player.pause();
  const transcript = el('details', {}, el('summary', {}, 'Ver transcripción y traducción'),
    scene.dialogue.map((line, order) => el('div', {class: 'audio-line'},
      el('div', {}, el('span', {lang: line.lang || scene.lang}, line.text), el('small', {}, line.es)),
      button('Escuchar', () => play(order)))));
  return [el('section', {class: 'panel'}, el('h3', {}, 'Escucha la escena'),
    el('div', {class: 'row'}, button('Reproducir diálogo', () => play(0, true), true), speed),
    player, status, transcript), quizView(scene, 'listening')];
}

function speakingView(scene, index, reviewMode = false, freeMode = false) {
  const turn = scene.turns[index];
  const status = statusNode();
  const feedback = el('div', {role: 'status'});
  const input = el('textarea', {id: 'reply', lang: scene.lang, maxlength: freeMode ? '1500' : '2000',
    placeholder: 'Escribe o revisa aquí lo que dijiste.'});
  input.value = state.pendingTalkDraft ?? '';
  delete state.pendingTalkDraft;
  const comparison = el('audio', {controls: true, 'aria-label': 'Tu grabación'});
  const reference = el('audio', {controls: true, preload: 'none', 'aria-label': 'Audio de referencia'});
  const savedStatus = statusNode();
  let take;
  const save = button('Guardar en Mis grabaciones', async () => {
    if (!take) return;
    const current = take;
    save.disabled = true;
    try {
      await api('recordings/' + scene.id + '/' + index + '/' + current.id, current.samples);
      if (take === current) setStatus(savedStatus, 'Guardada en Mis grabaciones.');
    } catch (error) {
      if (take === current) { save.disabled = false; setStatus(savedStatus, error.message, true); }
    }
  });
  const comparisonPanel = el('section', {hidden: true}, el('strong', {}, 'Tu grabación'),
    comparison, save, savedStatus);
  const modelText = el('p', {lang: scene.lang}, turn.model);
  const translation = el('p', {class:'muted'}, turn.model_es);
  const referencePanel = el('section', {hidden: true}, el('strong', {}, 'Audio de referencia'), reference, modelText, translation);
  let repetition = false;
  const repeat = button('Practicar la frase exacta', () => {
    repetition = !repetition;
    repeat.setAttribute('aria-pressed', String(repetition));
    repeat.textContent = repetition ? 'Volver a la respuesta guiada' : 'Practicar la frase exacta';
    referencePanel.hidden = !repetition;
    feedback.replaceChildren();
    next.hidden = true;
    if (repetition) {
      reference.src = audioPath(scene, 'model', index);
      setStatus(status, 'Escucha el modelo e imítalo. Después compara lo que has dicho.');
    } else {
      reference.pause();
      setStatus(status, '');
    }
  });
  repeat.setAttribute('aria-pressed','false');
  const prompt = el('audio', {controls: true, preload: 'none', 'aria-label': 'Intervención del interlocutor',
    src: audioPath(scene, 'prompt', index)});
  for (const audio of [reference, prompt, comparison]) {
    audio.addEventListener('play', () => {
      for (const other of [reference, prompt, comparison]) if (other !== audio) other.pause();
    });
  }
  const recorder = startRecorder(status, input, comparison, scene.lang, state.catalog.voice[scene.lang],
    () => [prompt, comparison, reference].forEach(audio => audio.pause()),
    samples => {
      take = {id: crypto.randomUUID(), samples};
      comparisonPanel.hidden = false;
      save.disabled = false;
      setStatus(savedStatus, '');
    });
  const next = button(reviewMode ? 'Volver al repaso' : index < scene.turns.length - 1 ? 'Siguiente turno' : 'Continuar a lectura', () => {
    if (reviewMode) location.hash = '#repaso';
    else if (index < scene.turns.length - 1) { state.turn++; render(true); }
    else { state.section = 'reading'; render(true); }
  }, true);
  next.hidden = true;
  if (!reviewMode && !freeMode && state.imitation) {
    repeat.click();
    state.imitation = false;
  }
  const history = [];
  const chat = el('div', {role: 'log', 'aria-label': 'Conversación libre'});
  const send = el('button', {class: 'button primary', type: 'submit'}, freeMode ? 'Enviar a OpenAI' : 'Revisar respuesta');
  let attempt;
  const form = el('form', {onsubmit: async event => {
    event.preventDefault();
    if (recorder.isBusy()) {
      setStatus(status, 'Termina la grabación y revisa la transcripción primero.');
      return;
    }
    const text = input.value.trim();
    if (!text) { setStatus(status, 'Graba o escribe tu respuesta.'); input.focus(); return; }
    send.disabled = recorder.control.disabled = true;
    setStatus(status, freeMode ? 'Preparando una respuesta…' : 'Revisando…');
    try {
      if (freeMode) {
        const result = await api('conversation', {scene: scene.id, text, enabled: state.cloud, history: history.slice(-3)});
        history.push({learner: text, reply: result.reply});
        chat.append(el('section', {class: 'chat-turn'}, el('p', {lang: scene.lang}, 'Tú · ' + text),
          el('p', {lang: scene.lang}, result.reply),
          result.correction && el('p', {class: 'feedback'}, el('strong', {lang: scene.lang}, result.correction), ' ' + result.explanation)));
        input.value = '';
        input.focus();
      } else {
        const activity = (repetition ? 'repeat/' : reviewMode ? 'review/' : 'turn/') + index;
        if (attempt?.text !== text || attempt?.activity !== activity) attempt = {text, activity, id: crypto.randomUUID()};
        const result = await submit(scene, activity, {text}, attempt.id);
        feedbackPanel(feedback, result, scene.lang);
        reference.src = audioPath(scene, 'model', index);
        referencePanel.hidden = false;
        if (repetition) {
          feedback.append(wordsView(turn.model, text));
        } else {
          feedback.append(assessmentView(scene, 'speaking'));
          next.hidden = false;
        }
      }
      setStatus(status, '');
    } catch (error) { setStatus(status, error.message, true); }
    finally {
      send.disabled = false;
      recorder.control.disabled = !recorder.supported;
    }
  }}, el('label', {for: 'reply'}, 'Tu respuesta'), input, el('div', {class: 'row'}, send, next));
  state.dispose = () => {
    recorder.dispose();
    reference.pause();
    prompt.pause();
  };
  return el('section', {class: 'panel'},
    el('h3', {}, reviewMode ? 'Frase de repaso' : freeMode ? 'Conversación libre' : 'Turno ' + (index + 1) + ' de ' + scene.turns.length),
    el('p', {class: 'prompt', lang: scene.lang}, turn.prompt),
    el('p', {class: 'muted'}, turn.es), prompt,
    freeMode && el('p', {class: 'muted'}, 'Se envía a OpenAI el texto que confirmes y los últimos turnos. El audio se queda en tu Mac.'),
    freeMode && chat, el('div', {class: 'row'}, recorder.control, !freeMode && !reviewMode && repeat),
    el('div', {class: 'audio-comparison'}, comparisonPanel, referencePanel), status, form, feedback);
}

function writeView(scene) {
  const answer = el('textarea', {id: 'writing-input', lang: scene.lang, maxlength: '4000', required: true});
  const output = el('div', {role: 'status'});
  const send = el('button', {class: 'button primary', type: 'submit'}, 'Comparar con el ejemplo');
  return el('section', {class: 'panel'}, el('form', {onsubmit: async event => {
    event.preventDefault();
    send.disabled = true;
    try {
      const result = await submit(scene, 'writing', {text: answer.value.trim()}, crypto.randomUUID());
      feedbackPanel(output, result, scene.lang);
      output.append(assessmentView(scene, 'writing'),
        el('div', {class: 'row'}, button('Continuar a ejercicios', () => { state.section = 'drills'; render(true); }, true),
          button('Volver al inicio', () => { location.hash = '#inicio'; })));
    } catch (error) { output.textContent = error.message; }
    finally { send.disabled = false; }
  }}, el('label', {for: 'writing-input'}, scene.writing.prompt), answer, send, output));
}

function showScene(scene) {
  setLanguage(scene.lang);
  setLevel(scene.level);
  const tabs = el('nav', {class: 'tabs', 'aria-label': 'Actividades de la escena'},
    sections.map(([value, text]) => el('button', {type: 'button',
      'aria-pressed': state.section === value ? 'true' : 'false',
      onclick: () => { state.section = value; render(); app.querySelector('.tabs [aria-pressed=true]').focus(); }}, text)));
  app.append(el('a', {class: 'back', href: '#inicio'}, 'Volver a las escenas'),
    el('div', {class: 'lesson-title'}, el('p', {class: 'kicker'}, languages[scene.lang][2] + ' · ' + scene.level + ' · Semana ' + scene.week),
      el('h1', {}, scene.title), el('p', {class: 'muted'}, scene.setup)), tabs);
  if (state.section === 'listening') app.append(...listeningView(scene));
  if (state.section === 'reading') app.append(quizView(scene, 'reading'));
  if (state.section === 'writing') app.append(writeView(scene));
  if (state.section === 'drills') app.append(exerciseView(scene, state.drill));
  if (state.section === 'talk') {
    if (state.cloud && state.catalog.cloud) {
      app.append(el('div', {class: 'row mode-switch'},
        button(state.free ? 'Volver a guiada' : 'Cambiar a conversación libre', () => {
          state.pendingTalkDraft = app.querySelector('#reply')?.value;
          state.free = !state.free;
          render(true);
        })));
    }
    app.append(speakingView(scene, state.turn, false, !!state.free && state.cloud));
  }
}

const drillNames = {dictation:'Dictado', grammar:'Gramática', vocabulary:'Vocabulario'};

function drillFor(scene, index) {
  return index === 0
    ? {kind:'dictation', prompt:'Escucha el audio y escribe la frase completa.'}
    : scene.exercises[index - 1];
}

function exerciseView(scene, index, reviewMode = false) {
  const exercise = drillFor(scene, index);
  const activity = (reviewMode ? 'review-exercise/' : 'exercise/') + index;
  const output = el('div', {role:'status'});
  const answer = el('textarea', {id:'exercise-answer', lang:scene.lang, maxlength: '1000',
    required:true, spellcheck:'false', autocomplete:'off'});
  const audio = exercise.kind === 'dictation'
    ? el('audio', {controls:true, preload:'none', 'aria-label':'Escucha el dictado', src:audioPath(scene,'line',1)})
    : undefined;
  if (audio) state.dispose = () => audio.pause();
  const submitButton = el('button', {type:'submit', class:'button primary'}, 'Comprobar ejercicio');
  const next = button(reviewMode ? 'Volver al repaso' : index < scene.exercises.length ? 'Siguiente ejercicio' : 'Volver a la ruta', () => {
    if (reviewMode) location.hash = '#repaso';
    else if (index < scene.exercises.length) { state.drill++; render(true); }
    else location.hash = '#inicio';
  });
  next.hidden = true;
  const form = el('form', {onsubmit: async event => {
    event.preventDefault();
    const text = answer.value.trim();
    if (!text) { answer.focus(); return; }
    submitButton.disabled = true;
    try {
      const result = await submit(scene, activity, {text}, crypto.randomUUID());
      feedbackPanel(output, result, scene.lang);
      if (exercise.kind === 'dictation') output.append(wordsView(result.example, text));
      next.hidden = !reviewMode && result.status !== 'correct';
    } catch (error) { output.textContent = error.message; }
    finally { submitButton.disabled = false; }
  }}, el('label', {for:answer.id}, exercise.kind === 'grammar' ? 'Palabra o expresión que falta' : 'Tu respuesta'),
    answer, el('div', {class:'row'}, submitButton, next), output);
  const selector = !reviewMode && scene.exercises.length > 0 && el('div', {class:'row drill-picker', 'aria-label':'Ejercicios'},
    [drillFor(scene,0), ...scene.exercises].map((item, number) =>
      el('button', {type:'button', class:'button', 'aria-pressed':String(number === index), onclick:() => {
        state.drill = number;
        render();
        app.querySelector('.drill-picker [aria-pressed=true]').focus();
      }}, drillNames[item.kind] + (item.kind === 'vocabulary' ? ' ' + (number - 1) : ''))));
  return el('section', {class:'panel'}, selector, el('h3', {}, drillNames[exercise.kind]),
    el('p', {class:'prompt', lang: exercise.kind === 'grammar' ? scene.lang : 'es'}, exercise.prompt),
    exercise.kind === 'grammar' && !scene.checkpoint && el('p', {class:'muted'}, scene.dialogue[3].es),
    audio, form);
}

function showReview(parts) {
  const scene = state.catalog.scenes.find(item => item.id === parts[1]);
  const position = Number(parts[2]);
  const isExercise = parts[3] === 'ejercicio';
  const list = isExercise ? state.progress.exercises : state.progress.reviews;
  const review = list.find(item => item.scene === scene?.id && item.turn === position);
  if (scene && review) {
    app.append(el('a', {href: '#repaso', class: 'back'}, 'Volver al repaso'),
      el('h1', {}, scene.title), isExercise ? exerciseView(scene, position, true) : speakingView(scene, position, true));
    return;
  }
  const cards = [...state.progress.reviews.map(item => ({...item, exercise:false})),
    ...state.progress.exercises.map(item => ({...item, exercise:true}))].filter(item => item.scene.startsWith(state.lang + '-'));
  const card = item => {
    const lesson = state.catalog.scenes.find(entry => entry.id === item.scene);
    if (!lesson) return null;
    return el('a', {class:'level-card', href:'#repaso/' + item.scene + '/' + item.turn + (item.exercise ? '/ejercicio' : '')},
      el('span', {class:'level'}, lesson.level + ' · ' + (item.exercise ? drillNames[drillFor(lesson,item.turn).kind] : 'Conversación')),
      el('h3', {}, lesson.title),
      el('p', {}, item.exercise ? drillFor(lesson,item.turn).prompt : lesson.turns[item.turn].es),
      !item.due && el('span', {class:'caption'}, 'Próximo repaso · ' + item.date));
  };
  const due = cards.filter(item => item.due);
  const later = cards.filter(item => !item.due).sort((a,b) => a.date.localeCompare(b.date));
  app.append(el('div', {class:'intro'}, el('div', {}, el('h1', {}, 'Repaso'),
    el('p', {class:'muted'}, 'Alterna ejercicios y frases para retener lo que ya estudiaste.')), languagePicker()),
    el('div', {class:'section-head'}, el('h2', {}, 'Para hoy')),
    due.length ? el('div', {class:'level-grid'}, due.map(card)) : el('p', {class:'muted'}, 'Tu repaso está al día. Las frases y ejercicios aparecerán aquí después de practicarlos.'),
    later.length && el('details', {class:'panel review-later'}, el('summary', {}, 'Próximos repasos · ' + later.length),
      el('div', {class:'level-grid'}, later.map(card))));
}

function render(focus = false) {
  if (!state.catalog || !state.progress) return;
  state.dispose();
  state.dispose = () => {};
  const parts = location.hash.slice(1).split('/');
  const scene = parts[0] === 'escena' ? state.catalog.scenes.find(item => item.id === parts[1]) : null;
  const route = parts[0] || 'hoy';
  if (state.scene !== scene?.id) {
    state.scene = scene?.id;
    state.section = scene && completed(scene.id, 'listening') ? 'talk' : 'listening';
    state.turn = scene?.turns.findIndex((_, index) => !completed(scene.id, 'turn/' + index)) ?? 0;
    state.drill = 0;
    if (state.turn < 0) {
      state.turn = 0;
      if (scene && !completed(scene.id, 'reading')) state.section = 'reading';
      else if (scene && !completed(scene.id, 'writing')) state.section = 'writing';
      else if (scene) {
        const pending = Array.from({length:scene.exercises.length + 1})
          .findIndex((_, index) => !completed(scene.id, 'exercise/' + index));
        if (pending !== -1) { state.section = 'drills'; state.drill = pending; }
      }
    }
    state.free = false;
  }
  if (scene && state.route !== location.hash) {
    const section = parts[2];
    const index = Number(parts[3]);
    if (sections.some(([value]) => value === section)) state.section = section;
    if (section === 'talk' && Number.isInteger(index) && index >= 0 && index < scene.turns.length) {
      state.turn = index;
      state.imitation = parts[4] === 'imita';
    }
    if (section === 'drills' && Number.isInteger(index) && index >= 0 && index <= scene.exercises.length) state.drill = index;
  }
  state.route = location.hash;
  for (const [id, page] of [['today-link','hoy'],['course-link','curso'],['vocab-link','vocabulario'],['review-link','repaso'],['progress-link','progreso'],['voice-link','voz'],['practice-link','practica']]) {
    const link = document.querySelector('#' + id);
    if (link) link.setAttribute('aria-current', route === page || (page === 'inicio' && scene) ? 'page' : 'false');
  }
  document.querySelectorAll('audio').forEach(player => player.pause());
  app.replaceChildren();
  const selected = state.catalog.scenes.filter(item => item.lang === state.lang);
  if (scene) showScene(scene);
  else if (route === 'hoy') app.append(todayView({lang: state.lang, picker: languagePicker()}));
  else if (route === 'curso') app.append(courseView({lang: state.lang, picker: languagePicker()}));
  else if (route === 'leccion' && parts[1]) app.append(lessonView(parts[1], {lang: state.lang}));
  else if (route === 'vocabulario') app.append(vocabView({lang: state.lang, picker: languagePicker()}));
  else if (route === 'repaso') showReview(parts);
  else if (route === 'practica') {
    const view = fieldView({parts, lang:state.lang, scenes:selected, level:activeLevel(), data:state.field,
      progress:state.progress, canTranscribe:state.catalog.voice[state.lang], picker:languagePicker(),
      onDispose:cleanup => { state.dispose = cleanup; }});
    app.append(view);
  }
  else if (route === 'progreso') app.append(courseProgressView({lang: state.lang, picker: languagePicker()}));
  else if (route === 'detalle') {
    app.append(el('div', {class:'intro'}, el('h1', {}, 'Mi progreso detallado'), languagePicker()));
    app.append(el('a',{class:'button monthly-link',href:'#practica/controles'},'Control de 4 semanas'), reportView(state.lang, selected));
  }
  else if (route === 'voz') {
    app.append(el('div', {class:'intro'}, el('h1', {}, 'Mis grabaciones'), languagePicker()));
    const next = selected.find(item => item.level === activeLevel() && !completed(item.id, 'turn/0')) || selected[0];
    app.append(journalView(state.lang, selected, next));
  } else showHome();
  if (focus) {
    const title = app.querySelector('h1');
    title.setAttribute('tabindex', '-1');
    title.focus();
  }
}

const settings = document.querySelector('#settings-dialog');
const cloudOption = document.querySelector('#cloud-option');
document.querySelector('#settings').addEventListener('click', () => {
  if (!state.catalog) return;
  cloudOption.disabled = !state.catalog.cloud;
  cloudOption.checked = state.cloud && state.catalog.cloud;
  document.querySelector('#cloud-help').textContent = state.catalog.cloud
    ? 'Envía la respuesta escrita que confirmes. Los diálogos guiados siguen disponibles sin internet.'
    : 'Para usar esta opción, inicia el servidor con una clave OPENAI_API_KEY.';
  settings.showModal();
});
cloudOption.addEventListener('change', () => {
  state.cloud = cloudOption.checked;
  localStorage.setItem('idiomas.cloud', String(state.cloud));
  if (state.section === 'talk') render();
});
function refreshDashboard(focus = false) {
  const route = location.hash;
  if (!state.progress || !['', '#inicio', '#repaso', '#progreso', '#voz'].includes(route)) {
    if (focus) render(true);
    return;
  }
  refreshProgress().catch(() => {}).then(() => {
    if (location.hash === route) render(focus);
  });
}

window.addEventListener('hashchange', () => refreshDashboard(true));
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible') refreshDashboard();
});
Promise.all([api('catalog'), refreshProgress(), loadField()])
  .then(([catalog, , field]) => { state.catalog = catalog; state.field = field; render(); })
  .catch(error => { app.textContent = error.message; });
