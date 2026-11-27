import {el, api} from './ui.js';
import {checkMenu, openCheck, workshopMenu, openWorkshop} from './field-checks.js';
import {coachMenu, openCoach} from './coach.js';

export async function loadField() {
  const response = await fetch('/assets/field-data.json');
  if (!response.ok) throw new Error('No se pudo cargar el taller de práctica.');
  return response.json();
}

function header(picker) {
  return el('div', {class: 'intro'},
    el('div', {},
      el('h1', {}, 'Práctica de campo'),
      el('p', {class: 'muted'}, 'Simulaciones, controles y pronunciación con grabaciones humanas.')),
    picker);
}

function card(href, kicker, title, copy, caption) {
  return el('a', {class: 'level-card', href},
    el('span', {class: 'level'}, kicker),
    el('h3', {}, title),
    el('p', {}, copy),
    el('span', {class: 'caption'}, caption));
}

export function fieldView({parts, lang, data, canTranscribe, picker, onDispose}) {
  let viewCleanup = () => {};
  onDispose(() => viewCleanup());
  const shell = el('div', {class: 'course'});
  const body = el('div', {}, el('p', {class: 'status'}, 'Cargando tu historial…'));
  shell.append(header(picker), body);

  api('field-history/' + lang).then(history => {
    const context = {lang, canTranscribe, onDispose: fn => { viewCleanup = fn; }};
    const route = parts[1] || 'hoy';
    const cases = data.cases.filter(item => item.lang === lang);
    const checks = data.checks.filter(item => item.lang === lang);
    const workshop = data.workshop.filter(item => item.lang === lang);

    function menu() {
      const conversations = history.items.filter(item => item.kind === 'coach').length;
      const controls = history.items.filter(item => item.kind === 'monthly').length;
      const sounds = history.items.filter(item => item.kind === 'workshop').length;
      return el('div', {},
        el('section', {class: 'stat-grid'},
          el('div', {class: 'stat-card'}, el('strong', {}, cases.length), el('span', {}, 'simulaciones'), el('small', {}, conversations ? conversations + ' intentos guardados' : 'Sin empezar')),
          el('div', {class: 'stat-card'}, el('strong', {}, checks.length), el('span', {}, 'controles'), el('small', {}, controls ? controls + ' intentos guardados' : 'Sin empezar')),
          el('div', {class: 'stat-card'}, el('strong', {}, workshop.length), el('span', {}, 'talleres de voz'), el('small', {}, sounds ? sounds + ' autoevaluaciones' : 'Sin empezar'))),
        el('section', {class: 'panel'},
          el('h2', {}, 'Elige una práctica'),
          el('div', {class: 'level-grid'},
            card('#practica/conversar', 'Conversación', 'Simulaciones guiadas', 'Cambiar una cita, resolver un problema, pedir una aclaración.', 'Responder con tus palabras'),
            card('#practica/controles', 'Evaluación', 'Controles de cuatro semanas', 'Escucha, lectura, conversación y escritura con rúbrica.', 'Medir el progreso'),
            card('#practica/voz', 'Pronunciación', 'Taller de sonidos', 'Pares mínimos y rasgos difíciles con voces de referencia.', 'Escuchar y grabarte'))),
        el('section', {class: 'panel'},
          el('h2', {}, 'Cómo encaja con el curso'),
          el('p', {}, 'El curso diario construye la base. Esta sección es el laboratorio: úsala cuando quieras medirte o practicar una situación concreta.'),
          el('div', {class: 'row'},
            el('a', {class: 'button primary', href: '#hoy'}, 'Volver a la sesión de hoy'),
            el('a', {class: 'button', href: '#curso'}, 'Ver el curso'))));
    }

    let view;
    if (route === 'controles' && parts[2]) {
      const test = checks.find(item => item.id === parts[2]);
      view = test ? openCheck(test, context, history) : el('p', {class: 'status error'}, 'Ese control no existe.');
    } else if (route === 'controles') {
      view = checkMenu(checks, history);
    } else if (route === 'conversar' && parts[2]) {
      const item = cases.find(entry => entry.id === parts[2]);
      view = item ? openCoach(item, context, history) : el('p', {class: 'status error'}, 'Esa simulación no existe.');
    } else if (route === 'conversar') {
      view = coachMenu(cases, history);
    } else if (route === 'voz' && parts[2]) {
      const lesson = workshop.find(entry => entry.id === parts[2]);
      view = lesson ? openWorkshop(lesson, context) : el('p', {class: 'status error'}, 'Ese taller no existe.');
    } else if (route === 'voz') {
      view = workshopMenu(workshop, history);
    } else {
      view = menu();
    }
    body.replaceChildren(view);
  }).catch(error => { body.textContent = error.message; });

  return shell;
}
