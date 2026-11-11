const keys = {ArrowUp: 'north', z: 'north', ArrowRight: 'east', d: 'east', ArrowDown: 'south', s: 'south', ArrowLeft: 'west', q: 'west', ' ': 'wait', Escape: 'quit'};
export function keyAction(event) {
  if (event.repeat || event.ctrlKey || event.metaKey || event.altKey || event.isComposing) return null;
  if (event.target?.closest?.('input, textarea, select, button, a, [contenteditable="true"], [role="textbox"]')) return null;
  return keys[event.key] ?? keys[event.key?.toLowerCase()] ?? null;
}
