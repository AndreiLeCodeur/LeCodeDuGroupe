// Teacher-only reference world. Never imported by the browser or the Python kit.
import {randomUUID} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {ACTIONS} from '../src/state.js';

export class DemoWorld {
  constructor() {
    this.state = JSON.parse(readFileSync(new URL('../fixtures/initial.json', import.meta.url), 'utf8'));
    this.session = randomUUID(); this.revision = 0; this.running = true;
  }
  frame() { return structuredClone({protocol_version: 1, session_id: this.session, revision: this.revision, running: this.running, state: this.state}); }
  action(body) {
    const error = (status, code, message) => ({status, body: {error: {code, message}}});
    if (!body || typeof body !== 'object' || Array.isArray(body) || Object.keys(body).length !== 1 || typeof body.action !== 'string') return error(422, 'invalid_request', 'Provide exactly one string action field.');
    if (!ACTIONS.includes(body.action)) return error(422, 'invalid_action', `Unknown action: ${body.action}`);
    if (!this.running) return error(409, 'game_closed', 'The game has closed. Restart the demo server for a new game.');
    if (body.action === 'quit') { this.running = false; this.revision++; }
    else if (this.state.status === 'playing') {
      const [dx, dy] = ({north: [0, -1], east: [1, 0], south: [0, 1], west: [-1, 0], wait: [0, 0]})[body.action];
      const player = this.state.entities.find(e => e.id === this.state.player_id);
      const x = player.x + dx, y = player.y + dy;
      const tile = this.state.level.tiles[y]?.[x];
      if (tile && tile !== 'wall') { player.x = x; player.y = y; }
      this.state.turn++; this.revision++;
      if (this.state.level.tiles[player.y][player.x] === 'exit') { this.state.status = 'won'; this.state.message = 'Victory!'; }
    }
    return {status: 200, body: this.frame()};
  }
}
