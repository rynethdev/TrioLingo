import {el, button, setStatus, statusNode} from './ui.js';
import {audioPlayer, localAnswer, panelTitle, recordField} from './field-ui.js';

const expressions = {
  lb: {repeat:['widderhuelen','nach eng kéier','méi lues'], reject:['kann net','passt net','geet net','eng aner','leider net','net kommen'], hour:'um'},
  da: {repeat:['gentage','igen','langsommere'], reject:['kan ikke','passer ikke','går ikke','en anden','desværre ikke'], hour:'klokken'},
  fr: {repeat:['répéter','plus lentement','redire','pardon'], reject:['ne peux pas','peux pas','ça ne va pas','ne me convient pas','un autre','une autre','pas disponible'], hour:'à'},
};

function normalize(text) {
  return text.toLowerCase().normalize('NFD').replace(/\p{M}+/gu,'')
    .replace(/[^\p{L}\p{N}]+/gu,' ').trim();
}

function contains(text, examples) {
  return examples.some(value => (' ' + text + ' ').includes(' ' + normalize(value) + ' '));
}

export function coachMenu(cases, history) {
  return el('div', {}, panelTitle('Elige una situación', 'Responde libremente. La otra persona puede pedirte que aclares algo u ofrecerte otra opción.'),
    el('div', {class:'level-grid'}, cases.map(item => {
      const previous = history.items.find(entry => entry.kind === 'coach' && entry.key === item.id);
      return el('a', {class:'level-card', href:'#practica/conversar/' + item.id},
        el('span', {class:'level'}, item.level), el('h3', {}, item.title),
        el('p', {}, item.setup), el('span',{class:'caption'}, previous ? 'Último intento · ' + previous.scores[0] + ' de 3 objetivos' : 'Iniciar simulación'));
    })));
}

export function openCoach(item, context, history) {
  const previous = history.items.find(entry => entry.kind === 'coach' && entry.key === item.id);
  const shell = el('div', {});
  let variant = previous ? (previous.variant + 1) % item.variants.length : 0;
  let completed = [];
  let cleanup = () => {};
  context.onDispose(() => cleanup());

  function start(withPlan = false) {
    cleanup();
    let step = 'request';
    let alternate = 0;
    let repair = false;
    let clarify = false;
    let requested = false;
    const slot = () => item.variants[variant][alternate];
    const grammar = expressions[item.lang];
    const lead = el('p', {class:'muted'}, item.setup);
    const historyList = el('ol', {class:'coach-log', 'aria-label':'Tus respuestas'});
    const body = el('section', {class:'panel coach-panel'});
    shell.replaceChildren(
      el('a',{class:'back',href:'#practica/conversar'},'Ver simulaciones'),
      el('h2',{},item.title), lead,
      withPlan && el('aside',{class:'feedback'},
        el('strong',{},'Tu segundo intento'),
        el('p',{},'Los horarios cambian. Pide lo que necesitas, escucha y confirma tanto el día como la hora.')),
      body, historyList);

    function reply(line) {
      cleanup();
      const player = audioPlayer(line, 'Escuchar intervención');
      const answer = localAnswer(item.lang, 'Tu respuesta', context.canTranscribe);
      const status = statusNode();
      cleanup = () => { player.audio.pause(); answer.dispose(); };
      const name = step === 'request' ? 'Explica por qué llamas' : 'Responde a la propuesta';
      const send = el('button', {type:'submit', class:'button primary'}, 'Responder');
      const form = el('form', {onsubmit: event => {
        event.preventDefault();
        if (answer.busy()) { setStatus(status, 'Termina primero la grabación.'); return; }
        const original = answer.input.value.trim();
        const text = normalize(original);
        if (!text) { setStatus(status, 'Graba o escribe tu respuesta.'); return; }
        if (contains(text, grammar.repeat)) { player.play.click(); setStatus(status, 'Escucha otra vez la intervención.'); return; }
        historyList.append(el('li', {}, el('strong', {}, 'Tú'), el('p', {lang:item.lang}, original)));
        if (step === 'request') {
          requested ||= contains(text, item.terms);
          if (!requested && !repair) { repair = true; reply(item.repair); return; }
          step = 'offer';
          reply(slot().line);
          return;
        }
        if (contains(text, grammar.reject) && alternate === 0) {
          alternate = 1;
          clarify = false;
          reply(slot().line);
          return;
        }
        const accepted = !contains(text, grammar.reject);
        const day = accepted && contains(text, [slot().day]);
        const time = accepted && contains(text, [slot().number, ...slot().aliases]);
        if ((!day || !time) && !clarify) { clarify = true; reply(item.clarify); return; }
        finish({requested, day, time}, slot());
      }}, answer.view, send, status);
      body.replaceChildren(el('h3',{},name), el('div',{class:'row'},player.play),
        player.audio, player.status, el('details', {}, el('summary',{},'Ver lo que dijo'),
          el('p',{lang:line.lang},line.text)), form);
    }

    function finish(outcome, offer) {
      cleanup();
      cleanup = () => {};
      const score = Number(outcome.requested) + Number(outcome.day) + Number(outcome.time);
      const corrections = [];
      if (!outcome.requested) corrections.push('Di primero por qué llamas. Prueba con la frase de apertura del ejemplo.');
      if (!outcome.day) corrections.push('Confirma el día que te ofrecieron: ' + offer.labels[0] + '.');
      if (!outcome.time) corrections.push('Confirma la hora exacta: ' + offer.labels[1] + '.');
      const model = offer.day + ' ' + grammar.hour + ' ' + offer.number;
      const status = statusNode();
      const id = crypto.randomUUID();
      const resultRows = [
        ['Explicaste el motivo', outcome.requested], ['Confirmaste el día', outcome.day], ['Confirmaste la hora', outcome.time],
      ];
      const retry = button(completed.length ? 'Volver a practicar con otros datos' : 'Hacer segundo intento', () => {
        completed.push(score);
        variant = (variant + 1) % item.variants.length;
        start(true);
      },true);
      retry.disabled = true;
      async function save() {
        try {
          await recordField(item.lang, item.id,'coach',{score,variant},id);
          setStatus(status,'Resultado guardado.');
        } catch (error) {
          setStatus(status,error.message,true);
          status.append(' ',button('Guardar otra vez',save));
        } finally { retry.disabled = false; }
      }
      body.replaceChildren(el('h3',{},'Resultado de la conversación'),
        el('strong',{class:'score-value'},score + ' de 3 objetivos reconocidos'),
        completed.length > 0 && el('p',{class:'muted'}, 'Intento anterior: ' + completed.at(-1) + ' de 3.'),
        el('ul',{class:'result-list'},resultRows.map(([label,met]) => el('li',{},label + ' · ' + (met ? 'Detectado' : 'Por revisar')))),
        corrections.length ? el('ol',{class:'feedback'},corrections.slice(0,2).map(correction=>el('li',{},correction)))
          : el('p',{class:'feedback'},'Confirmaste los datos y dejaste claro el motivo. Puedes repetir la escena para comprobarlo con otros horarios.'),
        el('div',{class:'model-snippet'},
          el('strong',{},'Frases modelo'), el('p',{lang:item.lang},item.sample), el('p',{lang:item.lang},model)),
        el('p',{class:'muted'},'La comprobación reconoce expresiones previstas. Revisa la transcripción y compara con el ejemplo si usaste otra formulación.'),
        el('div',{class:'row'},retry,el('a',{class:'button',href:'#practica/hoy'},'Volver a mi sesión')),status);
      save();
    }

    reply(item.opening);
  }

  start();
  return shell;
}
