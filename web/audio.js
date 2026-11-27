import {api, button, setStatus} from './ui.js';

export function startRecorder(status, input, comparison, lang, allow, beforeCapture, showRecording) {
  let capture;
  let disposed = false;
  let recording = false;
  let busy = false;
  let objectUrl;
  const control = button('Grabar respuesta', toggle);
  control.classList.add('recorder');
  control.setAttribute('aria-pressed', 'false');
  const supported = !!navigator.mediaDevices?.getUserMedia && !!window.AudioWorkletNode;
  control.disabled = !supported;
  if (!allow) setStatus(status, 'Puedes grabarte y escucharte. Activa el modelo de voz para transcribir la grabación.');
  if (!supported) {
    control.disabled = true;
    setStatus(status, 'Este navegador no tiene acceso al micrófono. Puedes escribir tu respuesta.');
  }

  function closeCapture() {
    if (!capture) return;
    const {stream, context, node, timer} = capture;
    clearTimeout(timer);
    if (node) node.port.onmessage = null;
    stream.getTracks().forEach(track => track.stop());
    context?.close().catch(() => {});
    capture = null;
  }

  async function toggle() {
    if (recording) return stop();
    control.disabled = true;
    busy = true;
    beforeCapture();
    setStatus(status, 'Esperando permiso del micrófono…');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({audio: {channelCount: 1}});
      if (disposed) {
        stream.getTracks().forEach(track => track.stop());
        return;
      }
      capture = {stream, chunks: [], length: 0};
      const context = new AudioContext();
      capture.context = context;
      await context.audioWorklet.addModule('/assets/recorder.js');
      if (disposed) return;
      const source = context.createMediaStreamSource(stream);
      const node = new AudioWorkletNode(context, 'idiomas-recorder', {channelCount: 1, channelCountMode: 'explicit'});
      capture.node = node;
      node.port.onmessage = ({data}) => {
        if (!capture || !recording) return;
        const remaining = Math.floor(context.sampleRate * 60) - capture.length;
        if (remaining <= 0) return;
        const part = data.subarray(0, remaining);
        capture.chunks.push(part);
        capture.length += part.length;
      };
      source.connect(node).connect(context.destination);
      await context.resume();
      if (disposed) return;
      recording = true;
      capture.timer = setTimeout(stop, 60_000);
      control.setAttribute('aria-pressed', 'true');
      control.textContent = 'Terminar grabación';
      setStatus(status, 'Grabando. Puedes hablar hasta un minuto.');
    } catch {
      closeCapture();
      busy = false;
      setStatus(status, 'No pudimos abrir el micrófono. Revisa el permiso o responde por escrito.', true);
    } finally {
      control.disabled = false;
    }
  }

  async function stop() {
    if (!recording || !capture) return;
    recording = false;
    control.disabled = true;
    control.setAttribute('aria-pressed', 'false');
    control.textContent = 'Grabar otra vez';
    const {chunks, length, context} = capture;
    const rate = context.sampleRate;
    closeCapture();
    if (length < rate / 4) {
      setStatus(status, 'Graba una respuesta un poco más larga.', true);
      control.disabled = false;
      busy = false;
      return;
    }
    setStatus(status, 'Preparando tu grabación…');
    try {
      const audio = new AudioBuffer({length, sampleRate: rate, numberOfChannels: 1});
      const channel = audio.getChannelData(0);
      let offset = 0;
      for (const chunk of chunks) { channel.set(chunk, offset); offset += chunk.length; }
      const offline = new OfflineAudioContext(1, Math.floor(length * 16_000 / rate), 16_000);
      const source = offline.createBufferSource();
      source.buffer = audio;
      source.connect(offline.destination);
      source.start();
      const pcm = (await offline.startRendering()).getChannelData(0);
      if (disposed) return;
      const samples = new ArrayBuffer(pcm.length * 2);
      const view = new DataView(samples);
      for (let index = 0; index < pcm.length; index++) {
        view.setInt16(index * 2, Math.min(32767, Math.max(-32768, pcm[index] * 32768)), true);
      }
      if (objectUrl) URL.revokeObjectURL(objectUrl);
      objectUrl = recordingUrl(samples);
      comparison.src = objectUrl;
      showRecording(samples);
      if (!allow) {
        setStatus(status, 'Puedes escuchar o guardar tu grabación.');
        return;
      }
      setStatus(status, 'Transcribiendo en tu Mac…');
      const result = await api('transcriptions/' + lang, samples);
      if (disposed) return;
      input.value = result.text;
      input.focus();
      setStatus(status, 'Revisa la transcripción antes de corregirla.');
    } catch (error) {
      if (!disposed) setStatus(status, error.message || 'No se pudo transcribir el audio.', true);
    } finally {
      busy = false;
      if (!disposed) control.disabled = false;
    }
  }

  return {control, supported, isBusy: () => busy, dispose: () => {
    disposed = true;
    closeCapture();
    comparison.pause();
    if (objectUrl) URL.revokeObjectURL(objectUrl);
  }};
}

function recordingUrl(samples) {
  const bytes = new DataView(new ArrayBuffer(44));
  for (const [offset, text] of [[0, 'RIFF'], [8, 'WAVEfmt '], [36, 'data']]) {
    [...text].forEach((letter, index) => bytes.setUint8(offset + index, letter.charCodeAt(0)));
  }
  for (const [offset, value] of [[4, samples.byteLength + 36], [16, 16], [24, 16000], [28, 32000], [40, samples.byteLength]]) {
    bytes.setUint32(offset, value, true);
  }
  for (const [offset, value] of [[20, 1], [22, 1], [32, 2], [34, 16]]) bytes.setUint16(offset, value, true);
  return URL.createObjectURL(new Blob([bytes, samples], {type: 'audio/wav'}));
}

