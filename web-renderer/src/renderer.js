import {copyState, sceneEntities} from './state.js';
import {keyAction} from './input.js';
import {loadSprites, loadModels} from './assets.js';
import {FlatView} from './flat-view.js';

const shell = `
  <header class="masthead">
    <div class="identity"><span class="sigil" aria-hidden="true">◇</span><div><p class="eyebrow">GRIDWORLD · AN INTERACTIVE EXPEDITION</p><h1>The ruins of Astraea</h1></div></div>
    <div class="view-switch" role="group" aria-label="View">
      <button type="button" data-view="3d" aria-pressed="true">Diorama <span>3D</span></button>
      <button type="button" data-view="2d" aria-pressed="false">Plan <span>2D</span></button>
    </div>
  </header>
  <section class="stage" aria-label="Game board">
    <div class="stage-top"><div><p class="eyebrow">THE EXPEDITION</p><h2 data-field="level">Awaiting a world</h2><p class="objective">Find your way to the glowing stairs.</p></div>
      <div class="view-tools"><div class="zoom-tools" role="group" aria-label="3D zoom"><button type="button" data-zoom="-.1" aria-label="Zoom out">−</button><button type="button" data-fit aria-label="Fit entire level">Fit</button><button type="button" data-zoom=".1" aria-label="Zoom in">+</button></div><button type="button" data-grid aria-pressed="false">Grid <kbd>G</kbd></button></div>
    </div>
    <div class="viewport" tabindex="0" aria-label="Game controls: arrows or Z Q S D to move, Space to wait, Escape to quit">
      <canvas data-canvas="3d" role="img" aria-label="3D game board"></canvas>
      <canvas data-canvas="2d" role="img" aria-label="2D game board" hidden></canvas>
      <p class="loading" data-field="loading">Preparing the expedition…</p>
    </div>
    <div class="stage-bottom"><span class="turn" data-field="turn">Turn: —</span><span class="game-status" data-field="status">Waiting for state</span><span data-field="inventory" hidden></span><span class="compass" aria-label="North is up. East is right.">N ↑ <span>·</span> E →</span></div>
  </section>
  <div class="readout"><p class="engine-message" data-field="message" aria-live="polite"></p><div class="telemetry"><span class="connection" data-field="connection" role="status">Local display</span><span class="coordinates" data-field="coordinates">—, —</span></div></div>
  <p class="diagnostic" data-field="diagnostic" role="status" hidden></p>
  <section class="sphinx-dialogue" data-field="dialogue" aria-labelledby="sphinx-title" hidden>
    <div class="dialogue-heading"><div><p class="eyebrow">THE GUARDIAN OF THE PASSAGE</p><h2 id="sphinx-title">The sphinx asks…</h2></div><span data-field="dialogue-status" role="status" aria-live="polite"></span></div>
    <p class="sphinx-question" data-field="question"></p>
    <p data-field="feedback" aria-live="polite"></p>
    <form data-answer-form>
      <label for="sphinx-answer">Your answer</label>
      <textarea id="sphinx-answer" name="answer" rows="2" required aria-describedby="answer-hint" placeholder="Explain your answer in your own words."></textarea>
      <p id="answer-hint">Up to 500 characters. The game waits while you answer.</p>
      <div class="dialogue-actions"><button type="submit" data-field="submit-answer">Send answer</button><button type="button" data-cancel>Close dialogue</button></div>
    </form>
  </section>
  <footer class="controls"><div class="movement" role="group" aria-label="Movement"><button type="button" data-action="north" aria-label="Move north">↑</button><button type="button" data-action="west" aria-label="Move west">←</button><button type="button" data-action="south" aria-label="Move south">↓</button><button type="button" data-action="east" aria-label="Move east">→</button></div><div class="action-buttons"><button type="button" data-action="wait">Wait <kbd>Space</kbd></button><button type="button" data-action="quit">Quit <kbd>Esc</kbd></button></div><p class="keyboard-hint">Move with <kbd>↑</kbd><kbd>←</kbd><kbd>↓</kbd><kbd>→</kbd> or <kbd>Z</kbd><kbd>Q</kbd><kbd>S</kbd><kbd>D</kbd><br><span>One press. One intention. Your engine decides.</span></p></footer>
  <div class="colophon"><span>One world. Two perspectives.</span><span>Art by Kenney · CC0 <span aria-hidden="true">/</span> Three.js · MIT</span></div>`;

export class GridWorldRenderer {
  constructor({view = '3d'} = {}) {
    if (!['2d', '3d'].includes(view)) throw new TypeError('View must be 2d or 3d.');
    this.view = view; this.requestedView = view; this.gridVisible = false; this.listeners = new Set();
    this.answerListeners = new Set(); this.cancelListeners = new Set(); this.busy = false;
    this.connection = 'local'; this.diagnostics = new Map(); this.events = new AbortController();
  }
  mount(container) {
    if (this.disposed) return Promise.reject(new Error('This renderer has been disposed.'));
    if (this.mountPromise) return this.mountPromise;
    this.mountPromise = this.initialize(container); return this.mountPromise;
  }
  async initialize(container) {
    this.root = document.createElement('div'); this.root.className = 'gridworld'; this.root.innerHTML = shell;
    container.append(this.root);
    this.fields = Object.fromEntries([...this.root.querySelectorAll('[data-field]')].map(element => [element.dataset.field, element]));
    this.viewport = this.root.querySelector('.viewport');
    this.canvas2d = this.root.querySelector('[data-canvas="2d"]');
    this.canvas3d = this.root.querySelector('[data-canvas="3d"]');
    this.answerInput = this.root.querySelector('[name="answer"]');
    this.answerForm = this.root.querySelector('[data-answer-form]');
    this.cancelButton = this.root.querySelector('[data-cancel]');
    const options = {signal: this.events.signal};
    this.answerInput.addEventListener('input', () => this.answerInput.setCustomValidity(''), options);
    this.answerForm.addEventListener('submit', event => {
      event.preventDefault();
      if (this.busy || !this.state?.interaction || !['question', 'rejected', 'error'].includes(this.state.interaction.status)) return;
      const answer = this.answerInput.value.trim();
      this.answerInput.setCustomValidity(!answer ? 'Enter an answer.' : [...answer].length > 500 ? 'Use at most 500 characters.' : '');
      if (!this.answerForm.reportValidity()) return;
      for (const callback of this.answerListeners) callback(this.state.interaction.id, answer);
    }, options);
    this.root.addEventListener('click', event => {
      const button = event.target.closest('button'); if (!button || button.disabled) return;
      if (button.closest('.sphinx-dialogue')) {
        if (button.hasAttribute('data-cancel') && this.state?.interaction) for (const callback of this.cancelListeners) callback(this.state.interaction.id);
        return;
      }
      if (button.dataset.action) this.emitAction(button.dataset.action);
      if (button.dataset.view) this.setView(button.dataset.view);
      if (button.hasAttribute('data-grid')) this.setGridVisible(!this.gridVisible);
      if (button.dataset.zoom) this.iso?.zoomBy(Number(button.dataset.zoom));
      if (button.hasAttribute('data-fit')) this.iso?.resetZoom();
      // Keep the game ready for the next arrow key after a pointer click.
      if (event.detail > 0) this.viewport.focus({preventScroll: true});
    }, options);
    this.root.addEventListener('keydown', event => {
      const action = keyAction(event);
      if (action) { event.preventDefault(); this.emitAction(action); }
      else if (event.key?.toLowerCase() === 'g' && !event.repeat && !event.ctrlKey && !event.metaKey && !event.altKey && !event.target.closest('button, input, textarea, select, a, [contenteditable]')) { event.preventDefault(); this.setGridVisible(!this.gridVisible); }
    }, options);
    this.refreshHUD();
    let sprites;
    try { sprites = await loadSprites(); }
    catch (error) { sprites = {sprites: new Map(), missing: ['all sprites']}; this.diagnostic('sprites', error.message); }
    if (this.disposed) return;
    this.flat = new FlatView(this.canvas2d, sprites.sprites);
    if (sprites.missing.length) this.diagnostic('sprites', `Missing 2D assets: ${sprites.missing.join(', ')}. Placeholders are shown.`);
    const requestedView = this.requestedView;
    this.setView('2d');
    this.requestedView = requestedView;
    // Restore the caller's requested mode after assets finish loading.
    this.view = this.requestedView ?? '3d';
    if (this.state) this.flat.update(this.state);
    try {
      const [{DioramaView}, models] = await Promise.all([import('./diorama-view.js'), loadModels()]);
      if (this.disposed) { models.dispose(); return; }
      this.models = models;
      this.iso = new DioramaView(this.canvas3d, models, message => this.fail3D(message));
      if (this.state) this.iso.update(this.state);
    } catch (error) {
      this.models?.dispose(); this.models = null;
      this.fail3D(`3D unavailable: ${error.message}. Using the 2D plan.`);
    }
    if (this.disposed) return;
    this.ready = true;
    this.setView(this.failed3D ? '2d' : this.view);
    this.setGridVisible(this.gridVisible);
    this.refreshHUD(); this.checkAppearances();
  }
  updateRender(value) {
    if (this.disposed) return;
    let next;
    try { next = copyState(value); }
    catch (error) { this.diagnostic('state', `Invalid state: ${error.message} Last valid image retained.`); return; }
    this.state = next; this.diagnostic('state', '');
    this.flat?.update(next); this.iso?.update(next);
    this.refreshHUD(); this.checkAppearances();
  }
  setView(mode) {
    if (!['2d', '3d'].includes(mode)) throw new TypeError('View must be 2d or 3d.');
    this.requestedView = mode;
    this.view = mode === '3d' && this.failed3D ? '2d' : mode;
    if (!this.root) return;
    this.canvas2d.hidden = this.view !== '2d'; this.canvas3d.hidden = this.view !== '3d';
    this.flat?.setActive(this.view === '2d'); this.iso?.setActive(this.view === '3d');
    for (const button of this.root.querySelectorAll('[data-view]')) {
      button.setAttribute('aria-pressed', String(button.dataset.view === this.view));
      button.disabled = button.dataset.view === '3d' && !!this.failed3D;
    }
    for (const button of this.root.querySelectorAll('[data-zoom], [data-fit]')) button.disabled = this.view !== '3d' || !this.iso;
  }
  setGridVisible(visible) {
    this.gridVisible = !!visible; this.flat?.setGridVisible(this.gridVisible); this.iso?.setGridVisible(this.gridVisible);
    this.root?.querySelector('[data-grid]')?.setAttribute('aria-pressed', String(this.gridVisible));
  }
  onAction(callback) { this.listeners.add(callback); return () => this.listeners.delete(callback); }
  onAnswer(callback) { this.answerListeners.add(callback); return () => this.answerListeners.delete(callback); }
  onCancel(callback) { this.cancelListeners.add(callback); return () => this.cancelListeners.delete(callback); }
  setBusy(busy) { this.busy = busy; this.refreshHUD(); }
  emitAction(action) {
    if (action !== 'quit' && this.state?.interaction && this.state.interaction.status !== 'accepted') return;
    if (this.state && ['connected', 'local'].includes(this.connection)) for (const callback of this.listeners) callback(action);
  }
  setConnection(status) {
    if (status !== this.connection && (status === 'connected' || status === 'closed')) this.diagnostic('network', '');
    this.connection = status;
    this.refreshHUD();
  }
  showError(message) { this.diagnostic('network', message); }
  diagnostic(key, message) {
    if (message) this.diagnostics.set(key, message); else this.diagnostics.delete(key);
    if (!this.fields) return;
    this.fields.diagnostic.textContent = [...this.diagnostics.values()].join(' ');
    this.fields.diagnostic.hidden = !this.diagnostics.size;
  }
  fail3D(message) { this.failed3D = true; this.diagnostic('3d', message); this.setView('2d'); }
  checkAppearances() {
    if (!this.state || !this.flat) return;
    const keys = [...sceneEntities(this.state).map(e => e.appearance), ...this.state.level.tiles.flat().filter(tile => tile !== 'exit')];
    const unknown = [...new Set(keys.filter(key => !this.flat.sprites.has(key)))];
    this.diagnostic('appearance', unknown.length ? `Placeholder for unknown or missing appearance: ${unknown.join(', ')}.` : '');
  }
  refreshHUD() {
    if (!this.fields) return;
    const {state, fields} = this;
    const labels = {local: 'Local display', connecting: 'Connecting…', connected: 'Connected', disconnected: 'Disconnected · retrying', closed: 'Game closed'};
    fields.connection.textContent = labels[this.connection] ?? this.connection;
    fields.connection.dataset.status = this.connection;
    const enabled = !!state && ['connected', 'local'].includes(this.connection);
    const paused = state?.interaction && state.interaction.status !== 'accepted';
    for (const button of this.root.querySelectorAll('[data-action]')) button.disabled = !enabled || (paused && button.dataset.action !== 'quit');
    this.refreshDialogue(enabled);
    fields.loading.hidden = !!state && !!this.flat;
    if (!state) return;
    const player = state.entities.find(entity => entity.id === state.player_id);
    fields.level.textContent = `Level ${state.level.id.toUpperCase()}`;
    fields.turn.textContent = `Turn: ${state.turn}`;
    fields.status.textContent = {playing: 'Reach the exit', won: 'Victory!', lost: 'Game over'}[state.status];
    fields.status.dataset.status = state.status;
    fields.message.textContent = state.message;
    fields.coordinates.textContent = `Player (${player.x}, ${player.y})`;
    fields.inventory.hidden = !Array.isArray(state.extras.inventory);
    if (!fields.inventory.hidden) fields.inventory.textContent = `Inventory: ${state.extras.inventory.map(item => typeof item === 'string' ? item : JSON.stringify(item)).join(', ') || 'empty'}`;
    const description = `${state.level.width} by ${state.level.height} board. Player at ${player.x}, ${player.y}. Turn: ${state.turn}. ${state.status}.`;
    this.canvas2d.setAttribute('aria-label', `2D ${description}`); this.canvas3d.setAttribute('aria-label', `3D ${description}`);
    this.root.dataset.gameStatus = state.status;
  }
  refreshDialogue(enabled) {
    const interaction = this.state?.interaction;
    const panel = this.fields.dialogue;
    if (!interaction) {
      if (!panel.hidden && panel.contains(document.activeElement)) this.viewport.focus({preventScroll: true});
      panel.hidden = true; this.dialogueId = null; return;
    }
    const fresh = interaction.id !== this.dialogueId;
    this.dialogueId = interaction.id;
    panel.hidden = false; panel.dataset.status = interaction.status;
    if (fresh) { this.answerInput.value = ''; this.answerInput.setCustomValidity(''); }
    this.fields.question.textContent = interaction.question;
    this.fields.feedback.textContent = interaction.message;
    const labels = {question: 'Your turn', pending: 'Evaluating your answer…', rejected: 'Try again', error: 'Evaluation unavailable · try again', accepted: 'Passage open'};
    this.fields['dialogue-status'].textContent = labels[interaction.status];
    const accepted = interaction.status === 'accepted';
    this.answerForm.hidden = accepted;
    this.answerInput.disabled = !enabled || this.busy || interaction.status === 'pending';
    this.fields['submit-answer'].disabled = this.answerInput.disabled;
    this.fields['submit-answer'].textContent = this.busy ? 'Sending…' : 'Send answer';
    this.cancelButton.disabled = !enabled || this.busy;
    if (fresh && enabled && !this.answerInput.disabled) this.answerInput.focus({preventScroll: true});
    if (accepted && panel.contains(document.activeElement)) this.viewport.focus({preventScroll: true});
  }
  dispose() {
    if (this.disposed) return;
    this.disposed = true; this.events.abort(); this.listeners.clear(); this.answerListeners.clear(); this.cancelListeners.clear();
    this.flat?.dispose(); this.iso?.dispose(); this.models?.dispose(); this.root?.remove(); this.state = null;
  }
}
