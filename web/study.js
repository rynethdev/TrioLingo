import {el, button, api, audioPath, setStatus, statusNode} from './ui.js';

export const levels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'];

const skills = {
  listening: 'Comprensión oral',
  reading: 'Comprensión escrita',
  speaking: 'Respuestas guiadas',
  dictation: 'Dictado',
  grammar: 'Gramática',
  vocabulary: 'Vocabulario',
  repetition: 'Repetición de frases',
};

const ratings = ['Me costó', 'Con ayuda', 'Sin ayuda'];

export function activitiesFor(scene) {
  return ['listening', 'reading', 'writing',
    ...scene.turns.map((_, index) => 'turn/' + index),
    ...Array.from({length: scene.exercises.length + 1}, (_, index) => 'exercise/' + index)];
}

function skillFor(activity, scene) {
  if (activity.startsWith('turn/')) return 'speaking';
  if (activity.startsWith('repeat/')) return 'repetition';
  if (activity.startsWith('exercise/')) {
    const index = Number(activity.split('/')[1]);
    return index === 0 ? 'dictation' : scene.exercises[index - 1]?.kind;
  }
  return activity;
}

function feedbackFocus(activity, scene) {
  const [kind, index] = activity.split('/');
  if (kind === 'listening' || kind === 'reading') return scene[kind].prompt;
  if (kind === 'turn' || kind === 'repeat') return scene.turns[Number(index)]?.es || scene.goal;
  if (kind === 'exercise' && index === '0') return 'Escucha y compara palabra por palabra.';
  return scene.exercises[Number(index) - 1]?.prompt || scene.goal;
}

function activityUrl(scene, activity) {
  const [kind, index] = activity.split('/');
  const section = kind === 'exercise' ? 'drills' : ['turn', 'repeat'].includes(kind) ? 'talk' : kind;
  return '#escena/' + scene + '/' + section + (index == null ? '' : '/' + index) + (kind === 'repeat' ? '/imita' : '');
}

export function assessmentView(scene, skill) {
  const status = statusNode();
  const controls = ratings.map((text, score) => button(text, async () => {
    controls.forEach(control => { control.disabled = true; });
    try {
      await api('assessments', {id: crypto.randomUUID(), scene: scene.id, activity: skill, score});
      controls.forEach((control, index) => control.setAttribute('aria-pressed', String(index === score)));
      setStatus(status, 'Autoevaluación guardada.');
    } catch (error) {
      setStatus(status, error.message, true);
    } finally {
      controls.forEach(control => { control.disabled = false; });
    }
  }));
  controls.forEach(control => control.setAttribute('aria-pressed', 'false'));
  return el('section', {class: 'reflection'},
    el('strong', {}, '¿Cómo te fue?'),
    el('p', {class: 'muted'}, skill === 'speaking'
      ? 'Escúchate y piensa si la idea se entiende con claridad. Ten en cuenta cuánto dependiste del ejemplo.'
      : 'Compara tu texto con el ejemplo y aplica el criterio de la actividad.'),
    el('div', {class: 'row'}, controls), status);
}

function localDate(date) {
  return [date.getFullYear(), date.getMonth() + 1, date.getDate()]
    .map(value => String(value).padStart(2, '0')).join('-');
}

function practiceCalendar(days, lang) {
  const key = 'idiomas.weekly-target.' + lang;
  const choose = el('select', {id: 'weekly-target'},
    [2, 3, 4, 5, 6, 7].map(n => el('option', {value: n}, n + ' días')));
  choose.value = localStorage.getItem(key) || '4';
  const dates = Array.from({length: 28}, (_, index) => {
    const date = new Date();
    date.setDate(date.getDate() - 27 + index);
    return localDate(date);
  });
  const active = dates.slice(-7).filter(date => days.includes(date)).length;
  const summary = el('p', {class: 'muted'});
  const refresh = () => {
    summary.textContent = active + ' de ' + choose.value + ' días de tu meta en los últimos 7 días.';
  };
  choose.addEventListener('change', () => { localStorage.setItem(key, choose.value); refresh(); });
  refresh();
  return el('section', {class: 'panel history-panel'}, el('h2', {}, 'Constancia'),
    el('div', {class: 'row'}, el('label', {for: choose.id}, 'Meta semanal'), choose), summary,
    el('ol', {class: 'calendar', 'aria-label': 'Últimos 28 días'},
      dates.map(date => el('li', {class: days.includes(date) ? 'studied' : '', title: date,
        'aria-label': date + (days.includes(date) ? ' con práctica' : ' sin práctica')}, date.slice(-2)))));
}

function scoreCard(title, results) {
  if (!results.length) return el('article', {class: 'score-card'}, el('h3', {}, title), el('p', {class:'muted'}, 'Aún sin ejercicios evaluados.'));
  const latest = results.filter(item => item.last === 'correct').length;
  const first = results.filter(item => item.first === 'correct').length;
  return el('article', {class: 'score-card'},
    el('h3', {}, title), el('strong', {class: 'score-value'}, latest + ' / ' + results.length),
    el('progress', {value: latest, max: results.length, 'aria-label': title + ', aciertos del último intento'}),
    el('p', {class: 'muted'}, 'Primer intento evaluado: ' + first + ' de ' + results.length + '.'));
}

export function reportView(lang, scenes) {
  const container = el('div', {}, el('p', {role:'status'}, 'Cargando tu progreso…'));
  const byId = new Map(scenes.map(scene => [scene.id, scene]));
  api('diagnostics/' + lang).then(report => {
    const measured = report.measurements.filter(item => byId.has(item.scene));
    const misses = measured.filter(item => item.last !== 'correct').slice(0, 5);
    const reflection = ['speaking', 'writing'].map(skill => {
      const samples = report.reflections.filter(item => item.activity === skill && byId.has(item.scene));
      const latest = samples[0];
      return el('article', {class: 'score-card'}, el('h3', {}, skill === 'speaking' ? 'Expresión oral · Tu valoración' : 'Escritura · Tu valoración'),
        latest
          ? el('div', {}, el('strong', {}, ratings[latest.score]), el('p', {class:'muted'}, byId.get(latest.scene).title + ' · ' + samples.length + ' escenas valoradas'))
          : el('p', {class:'muted'}, 'Completa una autoevaluación en una escena.'));
    });
    const controls = scenes.filter(scene => scene.checkpoint).map(scene => {
      const items = measured.filter(item => item.scene === scene.id && !item.activity.startsWith('repeat/'));
      const first = items.filter(item => item.first === 'correct').length;
      const latest = items.filter(item => item.last === 'correct').length;
      const possible = 3 + scene.turns.length + scene.exercises.length;
      return el('a', {class: 'level-card checkpoint-card', href:'#escena/' + scene.id},
        el('span', {class:'level'}, scene.level), el('strong', {}, scene.title.split(' · ').at(-1)),
        items.length > 0 && el('small', {class:'muted'}, items.length + ' de ' + possible + ' ejercicios medidos'),
        el('span', {class:'caption'}, items.length ? 'Primero ' + first + '/' + items.length + ' · Ahora ' + latest + '/' + items.length : 'Iniciar control'));
    });
    container.replaceChildren(
      el('section', {class: 'panel priority-panel'}, el('h2', {}, 'Qué mejorar ahora'),
        misses.length ? el('ul', {class: 'miss-list'}, misses.map(item => {
          const scene = byId.get(item.scene);
          const skill = skills[skillFor(item.activity, scene)] || 'Práctica';
          return el('li', {}, el('div', {}, el('strong', {}, skill), el('small', {}, scene.title),
            el('p', {class:'miss-focus', lang: skillFor(item.activity, scene) === 'grammar' ? scene.lang : 'es'}, feedbackFocus(item.activity, scene))),
            el('a', {class: 'button', href: activityUrl(scene.id, item.activity)}, 'Practicar'));
        })) : el('p', {class:'muted'}, measured.length ? 'Tus últimos intentos evaluados están correctos.' : 'Completa ejercicios para recibir recomendaciones.')),
      el('div', {class:'section-head'}, el('div', {}, el('h2', {}, 'Resultados por destreza'),
        el('p', {class:'muted'}, 'Cada ejercicio cuenta una vez. El resultado reciente se compara con tu primer intento en esos mismos ejercicios.'))),
      el('div', {class:'scores'}, Object.entries(skills).map(([skill, title]) =>
        scoreCard(title, measured.filter(item => skillFor(item.activity, byId.get(item.scene)) === skill))), reflection),
      practiceCalendar(report.days, lang),
      el('div', {class:'section-head'}, el('div', {}, el('h2', {}, 'Controles de nivel'),
        el('p', {class:'muted'}, 'Mide tu práctica con situaciones nuevas del itinerario.'))),
      el('div', {class:'level-grid'}, controls));
  }).catch(error => { container.textContent = error.message; });
  return container;
}

export function journalView(lang, scenes, nextScene) {
  const results = el('div', {}, el('p', {role:'status'}, 'Cargando tus grabaciones…'));
  const byId = new Map(scenes.map(scene => [scene.id, scene]));
  let page = 0;
  async function reload() {
    try {
      const {items, more} = await api('recordings/' + lang + '?page=' + page);
      if (!items.length && page > 0) { page--; return reload(); }
      const entries = items.length
        ? items.filter(item => byId.has(item.scene)).map((item, index) => {
          const scene = byId.get(item.scene);
          const message = statusNode();
          const tools = el('div', {class:'row'});
          const remove = button('Borrar', () => {
            const yes = button('Confirmar borrado', async () => {
              yes.disabled = true;
              try {
                await api('recording/' + item.id, undefined, 'DELETE');
                await reload();
              } catch (error) { setStatus(message, error.message, true); yes.disabled = false; }
            });
            tools.replaceChildren(yes, button('Cancelar', () => tools.replaceChildren(remove)));
          });
          tools.append(remove);
          const date = new Date(item.at.replace(' ', 'T') + 'Z').toLocaleDateString('es');
          const audio = el('audio', {controls:true, preload:'none', 'aria-label':'Tu voz', src:'/api/recording/' + item.id});
          const reference = el('audio', {controls:true, preload:'none', 'aria-label':'Referencia', src:audioPath(scene, 'model', item.turn)});
          const previous = items.slice(index + 1).find(entry => entry.scene === item.scene && entry.turn === item.turn);
          const older = previous && el('audio', {controls:true, preload:'none',
            'aria-label':'Tu grabación anterior', src:'/api/recording/' + previous.id});
          for (const player of [audio, reference, older].filter(Boolean)) player.addEventListener('play', () => {
            results.querySelectorAll('audio').forEach(other => { if (other !== player) other.pause(); });
          });
          return el('article', {class:'panel take'}, el('div', {class:'take-head'},
            el('div', {}, el('h3', {}, scene.title), el('p', {class:'muted'}, scene.level + ' · ' + date + ' · ' + (item.duration_ms / 1000).toFixed(1) + ' s')),
            el('a', {class:'text-link', href:activityUrl(scene.id, 'turn/' + item.turn)}, 'Practicar de nuevo')),
            el('div', {class:'audio-comparison'}, el('div', {}, el('strong', {}, 'Tu voz'), audio),
              el('div', {}, el('strong', {}, 'Referencia'), reference)),
            older && el('details', {}, el('summary', {}, 'Escuchar una toma anterior'), older), tools, message);
        }) : [el('p', {class:'muted'}, 'Cuando guardes una grabación desde una conversación, podrás escucharla aquí y compararla con la referencia.')];
      results.replaceChildren(...entries);
      if (page > 0 || more) {
        const previous = button('Página anterior', () => { page--; reload(); });
        previous.disabled = page === 0;
        const next = button('Página siguiente', () => { page++; reload(); });
        next.disabled = !more;
        results.append(el('div', {class:'row pagination'}, previous, next));
      }
    } catch (error) { results.textContent = error.message; }
  }
  reload();
  return el('div', {}, el('div', {class:'section-head'},
    el('a', {class:'button primary', href:activityUrl(nextScene.id,'turn/0')}, 'Practicar voz')), results);
}

function tokens(text) {
  return text.normalize('NFC').toLowerCase().replace(/['’ʼ]/g, '').match(/[\p{L}\p{N}]+/gu)?.slice(0, 80) || [];
}

function markedRow(title, list, unchanged, state) {
  return el('div', {}, el('strong', {}, title), el('p', {class:'word-row'},
    list.map((token, index) => el('span', {class: unchanged.has(index) ? '' : state}, token))));
}

export function wordsView(expected, submitted) {
  const a = tokens(expected), b = tokens(submitted);
  if (!b.length) return document.createDocumentFragment();
  const lengths = a.map(() => new Uint8Array(b.length + 1));
  const row = new Uint8Array(b.length + 1);
  for (let i = a.length - 1; i >= 0; i--) {
    const current = lengths[i], next = lengths[i+1] || row;
    for (let j = b.length - 1; j >= 0; j--) {
      current[j] = a[i] === b[j] ? next[j+1] + 1 : Math.max(next[j], current[j+1]);
    }
  }
  const first = new Set(), second = new Set();
  let i = 0, j = 0;
  while (i < a.length && j < b.length) {
    if (a[i] === b[j]) { first.add(i++); second.add(j++); }
    else if ((lengths[i+1] || row)[j] >= lengths[i][j+1]) i++;
    else j++;
  }
  return el('div', {class:'word-compare'},
    markedRow('Referencia', a, first, 'missing-word'),
    markedRow('Tu texto', b, second, 'extra-word'),
    el('small', {class:'muted'}, 'Se resaltan las palabras distintas en cada texto.'));
}
