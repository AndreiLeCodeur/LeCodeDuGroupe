import {GridWorldRenderer} from './src/renderer.js';
import {ApiClient} from './src/api-client.js';

const params = new URLSearchParams(location.search);
const renderer = new GridWorldRenderer({view: params.get('view') === '2d' ? '2d' : '3d'});
let client;
const input = document.querySelector('#api-url');
input.value = params.get('api') ?? '';
document.querySelector('#demo-note').hidden = !params.has('demo');
function connect() {
  const value = input.value.trim();
  if (value && !/^https?:\/\//i.test(value)) { renderer.showError('Use an HTTP or HTTPS API base URL.'); return; }
  client?.stop();
  client = new ApiClient({baseURL: value, onFrame: frame => renderer.updateRender(frame.state), onStatus: status => renderer.setConnection(status), onError: message => renderer.showError(message), onBusy: busy => renderer.setBusy(busy)});
  client.start();
}
renderer.onAction(action => client?.sendAction(action));
renderer.onAnswer((id, answer) => client?.sendAnswer(id, answer));
renderer.onCancel(id => client?.cancelInteraction(id));
document.querySelector('#connection-form').addEventListener('submit', event => {
  event.preventDefault();
  const url = new URL(location.href);
  if (input.value.trim()) url.searchParams.set('api', input.value.trim()); else url.searchParams.delete('api');
  history.replaceState(null, '', url); connect();
});
renderer.setConnection('connecting');
try { await renderer.mount(document.querySelector('#game')); connect(); }
catch (error) { renderer.showError(`Renderer could not start: ${error.message}`); }
window.addEventListener('pagehide', () => { client?.stop(); renderer.dispose(); }, {once: true});
// A page restored from the back-forward cache needs fresh resources and transport.
window.addEventListener('pageshow', event => { if (event.persisted) location.reload(); });
