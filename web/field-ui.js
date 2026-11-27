import {api, button, el, setStatus, statusNode} from './ui.js';
import {startRecorder} from './audio.js';

export function panelTitle(title, copy) {
  return el('div', {class:'section-head'}, el('div', {}, el('h2', {}, title),
    copy && el('p', {class:'muted'}, copy)));
}

export function localAnswer(lang, title, canTranscribe, leave, includeText = true) {
  const id = 'field-response';
  const input = el('textarea', {id, lang, maxlength:'1500', placeholder:'Escribe o revisa la transcripción.'});
  const status = statusNode();
  const audio = el('audio', {controls:true, hidden:true, 'aria-label':'Tu grabación'});
  const recorder = startRecorder(status, input, audio, lang, canTranscribe, () => {}, () => {
    audio.hidden = false;
  });
  if (!includeText) setStatus(status, '');
  if (leave) leave(recorder.dispose);
  return {
    input, audio, busy: recorder.isBusy, dispose:recorder.dispose,
    view: el('div', {class:'field-answer'}, recorder.control, audio, status,
      includeText && el('label', {for:id}, title), includeText && input),
  };
}

export function audioPlayer(line, name = 'Escuchar intervención') {
  const audio = el('audio', {controls:true, preload:'none', src:line.audio, 'aria-label':name, lang:line.lang});
  const status = statusNode();
  const play = button(name, async () => {
    try { await audio.play(); } catch { setStatus(status, 'Usa el control de audio para reproducir este fragmento.'); }
  });
  return {audio, play, status};
}

export function recordField(lang, key, kind, payload, id = crypto.randomUUID()) {
  return api('field-results', {id, lang, key, kind, ...payload});
}
