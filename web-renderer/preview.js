import {GridWorldRenderer} from './src/renderer.js';
const renderer = new GridWorldRenderer();
const select = document.querySelector('#fixture');
let generation = 0;
async function show() {
  const current = ++generation;
  if (select.value === 'invalid') { renderer.updateRender({level: {}}); return; }
  try {
    const response = await fetch(new URL(`fixtures/${select.value}.json`, import.meta.url));
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const state = await response.json();
    if (current === generation) renderer.updateRender(state);
  } catch (error) { renderer.showError(`Could not load fixture: ${error.message}`); }
}
renderer.onAction(action => { document.querySelector('#intent').textContent = `Intention: ${action}. The fixture is unchanged.`; });
renderer.onAnswer((id, answer) => { document.querySelector('#intent').textContent = `Answer intention for ${id}: ${answer}. The fixture is unchanged.`; });
renderer.onCancel(id => { document.querySelector('#intent').textContent = `Cancel intention for ${id}. The fixture is unchanged.`; });
select.addEventListener('change', show);
// Exercise updates arriving while mount is still loading assets.
const mounting = renderer.mount(document.querySelector('#game'));
await show(); await mounting;
window.addEventListener('pagehide', () => renderer.dispose(), {once: true});
window.addEventListener('pageshow', event => { if (event.persisted) location.reload(); });
