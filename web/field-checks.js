import {el, button, setStatus, statusNode} from './ui.js';
import {audioPlayer, localAnswer, panelTitle, recordField} from './field-ui.js';

const dayMs = 86_400_000;
const skillLabels = ['Escucha', 'Lectura', 'Conversación', 'Escritura'];

function scheduleLabel(test, history) {
  if (!history.started_on) return 'Programado para la semana ' + test.week;
  const due = Date.parse(history.started_on + 'T00:00:00Z') + (test.week - 1) * 7 * dayMs;
  const current = Date.parse(history.today + 'T00:00:00Z');
  if (current >= due) return 'Toca practicar';
  return 'Programado para el ' + new Date(due).toLocaleDateString('es', {timeZone:'UTC'});
}

export function checkMenu(checks, history) {
  return el('div', {}, panelTitle('Casos de cada cuatro semanas',
    'Haz un control en las semanas 4, 8, 12 y siguientes. Puedes abrirlo antes si quieres probar tu nivel.'),
    el('div', {class:'level-grid'},checks.map(test => {
      const last = history.items.find(entry => entry.kind === 'monthly' && entry.key === test.id);
      return el('a', {class:'level-card checkpoint-card',href:'#practica/controles/' + test.id},
        el('span',{class:'level'},test.level + ' · Semana ' + test.week),el('h3',{},test.title),
        el('p',{class:'muted'}, last ? 'Último intento · ' + last.day : scheduleLabel(test,history)),
        el('span',{class:'caption'},last ? 'Ver y volver a practicar' : 'Abrir control'));
    })));
}

function questions(items, kind) {
  return items.map((question,index) => el('fieldset',{class:'field-question'},
    el('legend',{},question.prompt),
    question.choices.map((text, choice) => el('label',{class:'choice'},
      el('input',{type:'radio',name:kind + index,value:choice,required:true}),text))));
}

function ratedCriteria(task, key, label, response) {
  const selected = task.criteria.map((criterion,index) => el('label',{class:'choice'},
    el('input',{type:'checkbox',name:key,value:index}),criterion));
  return el('div',{class:'panel'},
    el('h3',{},label),
    el('details',{},el('summary',{},'Ver mi respuesta'),el('p',{class:'prompt'},response)),
    el('p',{class:'muted'},'Lee el ejemplo y marca los criterios que cumpliste.'),
    el('p',{class:'prompt'},task.sample), selected);
}

function scoreRows(scores, previous) {
  return el('div',{class:'scores'}, scores.map((score, index) => el('article',{class:'score-card'},
    el('h3',{},skillLabels[index]),
    el('strong',{class:'score-value'},score + ' / 2'),
    el('p',{class:'muted'},index < 2 ? 'Respuestas correctas' : 'Criterios que valoraste'),
    previous && el('p',{class:'muted'},'Intento anterior: ' + previous.scores[index] + ' de 2'))));
}

export function openCheck(test, context, history) {
  const shell = el('div',{});
  let items = history.items.filter(entry => entry.kind === 'monthly' && entry.key === test.id);
  let cleanup = () => {};
  context.onDispose(() => cleanup());

  const heading = () => [
    el('a',{class:'back',href:'#practica/controles'},'Ver todos los controles'),
    el('p',{class:'kicker'},test.level + ' · Semana ' + test.week),
    el('h2',{},test.title),
  ];

  function start() {
    cleanup();
    const player = audioPlayer(test.listening.line, 'Escuchar situación');
    const oral = localAnswer(test.lang, 'Tu respuesta oral o su transcripción', context.canTranscribe);
    const written = el('textarea',{id:'check-writing',lang:test.lang,required:true,maxlength:'2400'});
    const status = statusNode();
    cleanup = () => {player.audio.pause(); oral.dispose();};
    const form = el('form', {onsubmit:event => {
      event.preventDefault();
      if (oral.busy()) { setStatus(status,'Termina primero la grabación.'); return; }
      const oralText = oral.input.value.trim();
      const writtenText = written.value.trim();
      if ((!oralText && !oral.audio.src) || !writtenText) { setStatus(status,'Completa la respuesta oral y la escrita.'); return; }
      const formData = new FormData(form);
      review({
        listening:[0,1].map(i=>Number(formData.get('listening'+i))),
        reading:[0,1].map(i=>Number(formData.get('reading'+i))),
      },oralText,writtenText,oral.audio);
    }},
    el('section',{class:'panel'},el('h3',{},'Escucha'),player.play,player.audio,player.status,questions(test.listening.questions,'listening')),
    el('section',{class:'panel'},el('h3',{},'Lectura'),
      el('p',{class:'prompt',lang:test.lang},test.reading.text),questions(test.reading.questions,'reading')),
    el('section',{class:'panel'},el('h3',{},'Conversación'),el('p',{},test.speaking.prompt),oral.view),
    el('section',{class:'panel'},el('h3',{},'Escritura'),el('label',{for:written.id},test.writing.prompt),written),
    el('div',{class:'row field-controls'},el('button',{type:'submit',class:'button primary'},'Revisar y autoevaluar'),status));
    shell.replaceChildren(...heading(),el('p',{class:'muted'},'Resuelve las cuatro partes. Verás los ejemplos y los criterios al terminar.'),form);
  }

  function review(scores, oral, written, audio) {
    const previous = items[0];
    const status = statusNode();
    const oralPanel = ratedCriteria(test.speaking,'speaking','Conversación',oral || 'Grabación oral');
    if (audio.src) { audio.hidden = false; oralPanel.prepend(audio); }
    const note = ratedCriteria(test.writing,'writing','Escritura',written);
    const save = el('button',{type:'submit',class:'button primary'},'Guardar control');
    const id = crypto.randomUUID();
    const form = el('form',{onsubmit:async event => {
      event.preventDefault();
      save.disabled = true;
      try {
        const data = new FormData(form);
        const result = await recordField(test.lang,test.id,'monthly',{
          ...scores, speaking:data.getAll('speaking').length, writing:data.getAll('writing').length,
        },id);
        items = [{scores:result.scores},...items];
        showResults(previous);
      } catch (error) { setStatus(status,error.message,true); save.disabled = false; }
    }},oralPanel,note,el('div',{class:'row field-controls'},save,status));
    shell.replaceChildren(...heading(),form);
  }

  function showResults(previous) {
    cleanup();
    cleanup = () => {};
    shell.replaceChildren(...heading(),panelTitle('Resultados del control',
      'Las partes de conversación y escritura reflejan tu propia valoración con los criterios de la tarea.'),
      scoreRows(items[0].scores,previous),
      el('section',{class:'panel field-controls'},el('h3',{},'Revisar comprensión'),
        el('details',{},el('summary',{},'Escucha y lectura · Soluciones'),
          [
            el('p',{class:'prompt',lang:test.lang},test.listening.line.text),
            ...test.listening.questions.map(item=>el('p',{},item.prompt + ' ' + item.choices[item.answer])),
            el('p',{class:'prompt',lang:test.lang},test.reading.text),
            ...test.reading.questions.map(item=>el('p',{},item.prompt + ' ' + item.choices[item.answer])),
          ])),
      el('div',{class:'row field-controls'},button('Repetir el control',start,true),
        el('a',{class:'button',href:'#practica/controles'},'Volver a los controles')));
  }

  if (items.length) showResults(items[1]);
  else start();
  return shell;
}

export function workshopMenu(lessons, history) {
  return el('div',{},panelTitle('Elige qué escuchar hoy','Cada ejercicio trabaja un sonido o un rasgo del ritmo con grabaciones humanas de referencia.'),
    el('div',{class:'level-grid'},lessons.map(lesson=>{
      const last = history.items.find(entry=>entry.kind === 'workshop' && entry.key === lesson.id);
      return el('a',{class:'level-card',href:'#practica/voz/' + lesson.id},el('h3',{},lesson.title),el('p',{},lesson.say),
        el('span',{class:'caption'}, last ? (last.scores[0] ? 'Lo distinguí' : 'Para volver a practicar') : 'Practicar'));
    })));
}

export function openWorkshop(lesson, context) {
  const listeners = lesson.clips.map(clip=>audioPlayer({audio:clip.audio,lang:lesson.lang},clip.label));
  const capture = localAnswer(lesson.lang,'',false,null,false);
  const players = [...listeners.map(item=>item.audio),capture.audio];
  for (const audio of players) audio.addEventListener('play',()=>{
    for (const other of players) if (other !== audio) other.pause();
  });
  context.onDispose(()=>{
    capture.dispose();
    for (const audio of players) audio.pause();
  });
  const status = statusNode();
  const rating = [button('Todavía me cuesta',()=>rate(0)),button('Oigo la diferencia',()=>rate(1),true)];
  async function rate(score) {
    rating.forEach(value=>{value.disabled = true;});
    try {
      await recordField(lesson.lang,lesson.id,'workshop',{score});
      setStatus(status,'Autoevaluación guardada.');
    } catch (error) { setStatus(status,error.message,true); }
    finally { rating.forEach(value=>{value.disabled = false;}); }
  }
  return el('div',{},
    el('a',{class:'back',href:'#practica/voz'},'Ver ejercicios de pronunciación'),
    el('h2',{},lesson.title),el('p',{class:'muted'},lesson.tip),
    el('section',{class:'panel'},el('h3',{},'Escucha las voces de referencia'),
      el('div',{class:'audio-comparison'},listeners.map((item,index)=>{
        const clip = lesson.clips[index];
        return el('div',{},item.play,item.audio,item.status,el('small',{class:'muted attribution'},
          el('a',{href:clip.source,target:'_blank',rel:'noopener noreferrer'},clip.credit), ' · ',
          el('a',{href:clip.license_url,target:'_blank',rel:'noopener noreferrer'},clip.license), ' · Conversión a MP3'));
      }))),
    el('section',{class:'panel'},el('h3',{},'Grábate y alterna las dos voces'),
      el('p',{class:'prompt',lang:lesson.lang},lesson.say),capture.view,
      el('p',{class:'muted'},'Escucha tu toma e indica si distingues el rasgo que practicaste.'),
      el('div',{class:'row'},rating),status));
}
