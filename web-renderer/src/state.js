export const ACTIONS = Object.freeze(['north', 'east', 'south', 'west', 'wait', 'quit']);
const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const integer = value => Number.isSafeInteger(value) && value >= 0;
const text = value => typeof value === 'string' && value.length > 0;

function requireValue(condition, message) {
  if (!condition) throw new TypeError(message);
}

// Reject non-JSON values before cloning; JSON.stringify alone silently loses data.
function checkJSON(value, ancestors = new Set()) {
  if (value === null || typeof value === 'string' || typeof value === 'boolean') return;
  if (typeof value === 'number' && Number.isFinite(value)) return;
  requireValue(Array.isArray(value) || (object(value) && Object.getPrototypeOf(value) === Object.prototype), 'State must contain ordinary JSON data.');
  requireValue(!ancestors.has(value), 'State must not contain circular references.');
  ancestors.add(value);
  for (const child of Array.isArray(value) ? value : Object.values(value)) checkJSON(child, ancestors);
  ancestors.delete(value);
}

export function copyState(value) {
  checkJSON(value);
  requireValue(object(value), 'State must be an object.');
  const {level, entities, player_id, status, turn, message, interaction, extras} = value;
  requireValue(object(level) && text(level.id), 'level.id must be a non-empty string.');
  requireValue(integer(level.width) && level.width > 0 && integer(level.height) && level.height > 0, 'Level dimensions must be positive integers.');
  requireValue(Array.isArray(level.tiles) && level.tiles.length === level.height && level.tiles.every(row => Array.isArray(row) && row.length === level.width && row.every(text)), 'tiles must match the level dimensions and contain tile names.');
  requireValue(Array.isArray(entities), 'entities must be an array.');
  const ids = new Set();
  for (const entity of entities) {
    requireValue(object(entity) && text(entity.id) && text(entity.kind) && text(entity.appearance), 'Each entity needs id, kind and appearance strings.');
    requireValue(!ids.has(entity.id), 'Entity IDs must be unique.');
    ids.add(entity.id);
    requireValue(integer(entity.x) && entity.x < level.width && integer(entity.y) && entity.y < level.height, 'Entity coordinates must be integers inside the level.');
  }
  requireValue(text(player_id) && entities.some(e => e.id === player_id && e.kind === 'player'), 'player_id must identify the player entity.');
  requireValue(['playing', 'won', 'lost'].includes(status), 'Unknown game status.');
  requireValue(integer(turn), 'turn must be a non-negative integer.');
  requireValue(typeof message === 'string', 'message must be a string.');
  requireValue(interaction === null || object(interaction), 'interaction must be null or an object.');
  if (interaction !== null) {
    const keys = ['id', 'actor_id', 'status', 'question', 'message'];
    requireValue(Object.keys(interaction).length === keys.length && keys.every(key => typeof interaction[key] === 'string'), 'Interaction must contain exactly id, actor_id, status, question and message strings.');
    requireValue(text(interaction.id) && text(interaction.actor_id) && text(interaction.question), 'Interaction identifiers and question must not be empty.');
    requireValue(['question', 'pending', 'rejected', 'error', 'accepted'].includes(interaction.status), 'Unknown interaction status.');
    requireValue(entities.some(entity => entity.id === interaction.actor_id), 'Interaction actor must exist.');
  }
  requireValue(object(extras), 'extras must be an object.');
  return JSON.parse(JSON.stringify(value));
}

export function copyFrame(frame) {
  requireValue(object(frame) && frame.protocol_version === 1, 'Expected StateFrame protocol_version 1.');
  requireValue(text(frame.session_id) && integer(frame.revision) && typeof frame.running === 'boolean', 'Invalid session_id, revision or running in StateFrame.');
  return {...frame, state: copyState(frame.state)};
}

export const terrainKey = state => JSON.stringify([state.level.id, state.level.width, state.level.height, state.level.tiles]);
const aliases = new Map([['player', 'player.idle'], ['potion', 'potion.idle'], ['exit', 'exit.idle']]);
export const appearance = name => aliases.get(name) ?? name;

// Pure presentation mapping: exits come from terrain, actors from entities.
export function sceneEntities(state) {
  const exits = [];
  state.level.tiles.forEach((row, y) => row.forEach((tile, x) => {
    if (tile === 'exit') exits.push({id: `tile:${x},${y}`, x, y, appearance: 'exit.idle'});
  }));
  const actors = state.entities.map(e => ({...e, id: `entity:${e.id}`, appearance: appearance(e.appearance)}));
  actors.sort((a, b) => (a.id === `entity:${state.player_id}`) - (b.id === `entity:${state.player_id}`));
  return [...exits, ...actors];
}

export function shouldAnimate(previous, next, previousTurn, nextTurn, sameLevel) {
  return sameLevel && nextTurn > previousTurn && Math.abs(previous.x - next.x) + Math.abs(previous.y - next.y) === 1;
}
