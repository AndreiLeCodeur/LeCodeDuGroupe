import {ACTIONS, copyFrame} from './state.js';

export class APIError extends Error {
  constructor(message, status = 0) { super(message); this.status = status; }
}

// Owns transport only. No drawing, keyboard handling or game rules.
export class ApiClient {
  constructor({baseURL = '', onFrame = () => {}, onStatus = () => {}, onError = () => {}, onBusy = () => {}, fetch: request = globalThis.fetch, pollInterval = 150, timeout = 5000} = {}) {
    this.baseURL = baseURL.replace(/\/$/, '');
    this.onFrame = onFrame; this.onStatus = onStatus; this.onError = onError; this.onBusy = onBusy;
    this.fetch = (...args) => request(...args); this.pollInterval = pollInterval; this.timeout = timeout;
    this.epoch = 0; this.controllers = new Set(); this.retired = new Set();
    this.queue = []; this.stopped = true; this.connected = false;
  }
  start() {
    this.stop();
    this.stopped = false; this.session = null; this.revision = -1; this.running = false; this.interaction = null;
    this.retired.clear(); this.onStatus('connecting'); this.poll();
  }
  stop() {
    this.stopped = true; this.connected = false; this.invalidate();
  }
  invalidate() {
    this.epoch++;
    clearTimeout(this.timer);
    for (const controller of this.controllers) controller.abort();
    this.controllers.clear(); this.queue = []; this.getBusy = false; this.postBusy = false; this.onBusy(false);
  }
  async request(path, options = {}, expectedStatus = 200) {
    const controller = new AbortController(); this.controllers.add(controller);
    const timer = setTimeout(() => controller.abort(), this.timeout);
    try {
      const response = await this.fetch(`${this.baseURL}${path}`, {...options, signal: controller.signal, cache: 'no-store', headers: {Accept: 'application/json', ...options.headers}});
      let data;
      try { data = await response.json(); }
      catch { throw new APIError(`API returned invalid JSON (HTTP ${response.status}).`, response.status); }
      if (response.status !== expectedStatus) throw new APIError(data?.error?.message || `API returned HTTP ${response.status}; expected ${expectedStatus}.`, response.status);
      const frame = copyFrame(data);
      if (path === '/api/answer' && frame.state.interaction?.status !== 'pending') throw new APIError('An accepted submission must return the pending state.', response.status);
      return frame;
    } finally { clearTimeout(timer); this.controllers.delete(controller); }
  }
  accept(frame, source) {
    if (this.retired.has(frame.session_id)) return false;
    if (this.session && frame.session_id !== this.session) {
      this.retired.add(this.session);
      this.session = null; this.revision = -1; this.running = false; this.connected = false;
      this.invalidate(); this.onStatus('connecting');
      this.timer = setTimeout(() => this.poll(), 0);
      return false;
    }
    // The first frame for any session must be confirmed by GET.
    if (!this.session && source !== 'GET') return false;
    if (!this.session) this.session = frame.session_id;
    if (frame.revision < this.revision) return false;
    if (frame.revision > this.revision) {
      this.revision = frame.revision; this.running = frame.running;
      this.interaction = frame.state.interaction;
      if (this.interaction && this.interaction.status !== 'accepted') {
        // Movement typed before the encounter must not execute after the dialogue.
        this.queue = this.queue.filter(command => command.path !== '/api/actions' || command.body.action === 'quit');
      }
      this.onFrame(frame);
    }
    this.connected = true;
    if (!this.running) this.queue = [];
    this.onStatus(this.running ? 'connected' : 'closed');
    return true;
  }
  disconnect(error) {
    this.connected = false; this.queue = [];
    this.onError(error.message); this.onStatus('disconnected');
  }
  async poll() {
    if (this.stopped || this.getBusy) return;
    clearTimeout(this.timer);
    this.getBusy = true;
    const epoch = this.epoch;
    try {
      const frame = await this.request('/api/state');
      if (epoch === this.epoch && !this.stopped) this.accept(frame, 'GET');
    } catch (error) {
      if (epoch === this.epoch && !this.stopped) this.disconnect(error);
    } finally {
      if (epoch === this.epoch && !this.stopped) {
        this.getBusy = false;
        this.timer = setTimeout(() => this.poll(), this.connected ? this.pollInterval : 1000);
      }
    }
  }
  sendAction(action) {
    if (!ACTIONS.includes(action)) throw new TypeError(`Unknown action: ${action}`);
    if (action !== 'quit' && this.interaction && this.interaction.status !== 'accepted') return false;
    return this.enqueue('/api/actions', {action});
  }
  sendAnswer(interactionId, answer) {
    if (typeof answer !== 'string' || !answer.trim() || [...answer.trim()].length > 500) return false;
    if (this.postBusy || this.interaction?.id !== interactionId || !['question', 'rejected', 'error'].includes(this.interaction?.status)) return false;
    return this.enqueue('/api/answer', {interaction_id: interactionId, answer: answer.trim()}, 202);
  }
  cancelInteraction(interactionId) {
    if (this.postBusy || this.interaction?.id !== interactionId || this.interaction.status === 'accepted') return false;
    return this.enqueue('/api/cancel', {interaction_id: interactionId});
  }
  enqueue(path, body, expectedStatus = 200) {
    if (this.stopped || !this.connected || !this.running) return false;
    this.queue.push({path, body, expectedStatus}); this.drain(); return true;
  }
  async drain() {
    if (this.postBusy || this.stopped || !this.connected || !this.running || !this.queue.length) return;
    this.postBusy = true; this.onBusy(true);
    const epoch = this.epoch, command = this.queue.shift();
    try {
      const frame = await this.request(command.path, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(command.body)}, command.expectedStatus);
      if (epoch === this.epoch && !this.stopped && this.accept(frame, 'POST')) this.onError('');
    } catch (error) {
      if (epoch === this.epoch && !this.stopped) {
        this.queue = [];
        if ([400, 415, 422].includes(error.status)) this.onError(error.message);
        else {
          // Abort stale reads too: only a new GET can restore control after an uncertain POST.
          this.invalidate(); this.disconnect(error);
          this.timer = setTimeout(() => this.poll(), error.status === 409 ? 0 : 1000);
        }
      }
    } finally {
      if (epoch === this.epoch && !this.stopped) { this.postBusy = false; this.onBusy(false); this.drain(); }
    }
  }
}
