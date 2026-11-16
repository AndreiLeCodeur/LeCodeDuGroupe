import {sceneEntities} from './state.js';

export class FlatView {
  constructor(canvas, sprites) {
    this.canvas = canvas;
    this.sprites = sprites;
    this.context = canvas.getContext('2d');
    if (!this.context) throw new Error('Canvas 2D is unavailable.');
    this.observer = new ResizeObserver(() => this.draw());
    this.observer.observe(canvas.parentElement);
  }
  update(state) { this.state = state; this.draw(); }
  setGridVisible(visible) { this.grid = visible; this.draw(); }
  setActive(active) { this.active = active; if (active) this.draw(); }
  draw() {
    if (!this.state || !this.active) return;
    const {width, height, tiles} = this.state.level;
    const rect = this.canvas.parentElement.getBoundingClientRect();
    const dpr = Math.min(devicePixelRatio || 1, 2);
    this.canvas.width = Math.round(rect.width * dpr);
    this.canvas.height = Math.round(rect.height * dpr);
    const ctx = this.context;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.imageSmoothingEnabled = false;
    ctx.clearRect(0, 0, rect.width, rect.height);
    const cell = Math.max(1, Math.floor(Math.min((rect.width - 32) / width, (rect.height - 32) / height)));
    const left = Math.floor((rect.width - width * cell) / 2), top = Math.floor((rect.height - height * cell) / 2);
    ctx.shadowColor = '#0009'; ctx.shadowBlur = 24;
    ctx.fillStyle = '#344354'; ctx.fillRect(left - 5, top - 5, width * cell + 10, height * cell + 12);
    ctx.shadowBlur = 0;
    const sprite = (key, x, y) => {
      const image = this.sprites.get(key);
      const px = left + x * cell, py = top + y * cell;
      if (image) ctx.drawImage(image, px, py, cell, cell);
      else {
        ctx.fillStyle = '#6f406c'; ctx.fillRect(px + cell * .12, py + cell * .12, cell * .76, cell * .76);
        ctx.fillStyle = '#fff'; ctx.font = `bold ${Math.max(10, cell * .55)}px sans-serif`;
        ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('?', px + cell / 2, py + cell / 2);
      }
    };
    tiles.forEach((row, y) => row.forEach((tile, x) => {
      sprite('floor', x, y);
      if (tile !== 'floor' && tile !== 'exit') sprite(tile, x, y);
    }));
    if (this.grid) {
      ctx.strokeStyle = '#a9eedb88'; ctx.lineWidth = 1;
      for (let x = 0; x <= width; x++) { ctx.beginPath(); ctx.moveTo(left + x * cell, top); ctx.lineTo(left + x * cell, top + height * cell); ctx.stroke(); }
      for (let y = 0; y <= height; y++) { ctx.beginPath(); ctx.moveTo(left, top + y * cell); ctx.lineTo(left + width * cell, top + y * cell); ctx.stroke(); }
    }
    for (const entity of sceneEntities(this.state)) sprite(entity.appearance, entity.x, entity.y);
  }
  dispose() { this.observer.disconnect(); this.state = null; this.canvas.width = this.canvas.height = 0; }
}
