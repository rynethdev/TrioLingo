export function el(tag, props = {}, ...children) {
  const node = document.createElement(tag);
  for (const [name, value] of Object.entries(props)) {
    if (value === undefined || value === false) continue;
    if (name === 'class') node.className = value;
    else if (name.startsWith('on')) node.addEventListener(name.slice(2), value);
    else node.setAttribute(name, value === true ? '' : value);
  }
  node.append(...children.flat().filter(child => child != null && child !== false && child !== true));
  return node;
}

export function button(text, click, primary = false) {
  return el('button', {type: 'button', class: 'button' + (primary ? ' primary' : ''), onclick: click}, text);
}

export async function api(path, data, method) {
  const options = data === undefined ? {} : data instanceof ArrayBuffer
    ? {method: 'POST', headers: {'Content-Type': 'application/octet-stream'}, body: data}
    : {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)};
  if (method) options.method = method;
  const response = await fetch('/api/' + path, options);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.error || 'La app no pudo terminar la solicitud. Intenta de nuevo.');
  return body;
}

export function setStatus(node, message, error = false) {
  node.textContent = message;
  node.classList.toggle('error', error);
}

export function statusNode() {
  return el('p', {class: 'status', role: 'status'});
}

export function audioPath(scene, type, index) {
  return '/assets/audio/' + scene.id + '-' + type + '-' + index + '.mp3';
}

