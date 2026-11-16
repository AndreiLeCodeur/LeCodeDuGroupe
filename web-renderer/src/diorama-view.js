import * as THREE from '../vendor/three.module.js';
import {clone} from '../vendor/SkeletonUtils.js';
import {sceneEntities, terrainKey, shouldAnimate} from './state.js';

// Only presentation lives here: no network, collision checks or game clock.
export class DioramaView {
  constructor(canvas, assets, onFailure) {
    this.canvas = canvas;
    this.assets = assets;
    this.entities = new Map();
    this.effects = [];
    this.width = this.height = 1;
    this.zoom = 1;
    this.renderer = new THREE.WebGLRenderer({canvas, alpha: true, antialias: true});
    this.renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.3;
    this.scene = new THREE.Scene();
    this.camera = new THREE.OrthographicCamera(-10, 10, 8, -8, .1, 200);
    this.world = new THREE.Group();
    this.scene.add(this.world, new THREE.HemisphereLight(0xb9d8ff, 0x333044, 2.4));
    this.sun = new THREE.DirectionalLight(0xffdab0, 4.2);
    this.sun.position.set(-6, 12, 8);
    this.sun.castShadow = true;
    this.sun.shadow.mapSize.set(2048, 2048);
    this.sun.shadow.normalBias = .035;
    this.sun.shadow.bias = -.00015;
    this.sun.shadow.radius = 3;
    const rim = new THREE.DirectionalLight(0x779bff, 2.7);
    rim.position.set(3, 7, -9);
    this.scene.add(this.sun, rim);
    const positions = new Float32Array(65 * 3);
    for (let i = 0; i < 65; i++) {
      positions[i * 3] = Math.sin(i * 127.1) * 9;
      positions[i * 3 + 1] = .5 + (i % 13) * .25;
      positions[i * 3 + 2] = Math.cos(i * 81.3) * 6;
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    this.dust = new THREE.Points(geometry, new THREE.PointsMaterial({color: 0xf9dca3, size: .027, transparent: true, opacity: .6, depthWrite: false}));
    this.scene.add(this.dust);
    this.motion = matchMedia('(prefers-reduced-motion: reduce)');
    this.onVisibility = () => this.schedule();
    this.onMotion = () => { this.snap(); this.schedule(); };
    this.onContextLost = event => { event.preventDefault(); this.setActive(false); onFailure('WebGL context lost. Switched to the 2D plan.'); };
    document.addEventListener('visibilitychange', this.onVisibility);
    this.motion.addEventListener('change', this.onMotion);
    canvas.addEventListener('webglcontextlost', this.onContextLost);
    this.observer = new ResizeObserver(() => this.fit());
    this.observer.observe(canvas.parentElement);
  }

  model(name) {
    const root = clone(this.assets.models.get(name).scene);
    root.traverse(part => {
      if (part.isMesh) {
        part.userData.sharedAsset = true;
        part.castShadow = part.receiveShadow = true;
      }
    });
    return root;
  }
  mesh(geometry, material, parent, x = 0, y = 0, z = 0) {
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(x, y, z);
    mesh.castShadow = mesh.receiveShadow = true;
    parent.add(mesh);
    return mesh;
  }
  ring(parent, radius, color, elevation) {
    const ring = this.mesh(new THREE.TorusGeometry(radius, .016, 6, 40), new THREE.MeshBasicMaterial({color}), parent, 0, elevation, 0);
    ring.rotation.x = -Math.PI / 2;
    ring.castShadow = false;
  }
  release(root) {
    if (!root) return;
    const skeletons = new Set();
    root.traverse(part => {
      if (part.skeleton) skeletons.add(part.skeleton);
      if (!part.userData.sharedAsset) {
        part.geometry?.dispose();
        for (const material of Array.isArray(part.material) ? part.material : [part.material]) material?.dispose();
      }
    });
    skeletons.forEach(skeleton => skeleton.dispose());
    root.removeFromParent();
  }
  removeEntity(item) {
    item.mixer?.stopAllAction();
    item.mixer?.uncacheRoot(item.visual);
    this.release(item.root);
  }
  buildTerrain(state) {
    for (const item of this.entities.values()) this.removeEntity(item);
    this.entities.clear();
    this.release(this.board);
    this.effects = [];
    const {width, height, tiles} = state.level;
    this.width = width; this.height = height;
    this.zoom = 1;
    this.board = new THREE.Group();
    this.world.add(this.board);
    const stone = color => new THREE.MeshStandardMaterial({color, roughness: .9});
    this.mesh(new THREE.BoxGeometry(width + .14, .8, height + .14), stone(0x344354), this.board, 0, -.42);
    this.mesh(new THREE.BoxGeometry(width - .25, .12, height - .25), stone(0x1f2d3f), this.board, 0, -.85);
    this.mesh(new THREE.BoxGeometry(width + .21, .045, height + .21), new THREE.MeshStandardMaterial({color: 0xc8a66c, metalness: .5, roughness: .4}), this.board, 0, -.14);
    const place = (name, x, y, elevation = .01, scale = .97) => {
      const root = this.model(name);
      root.position.set(x - (width - 1) / 2, elevation, y - (height - 1) / 2);
      root.scale.setScalar(scale);
      this.board.add(root);
      return root;
    };
    tiles.forEach((row, y) => row.forEach((tile, x) => {
      const floor = place((x * 7 + y * 3) % 5 === 0 ? 'floor-detail.glb' : this.assets.manifest.floor.model, x, y);
      floor.rotation.y = ((x * 3 + y) % 4) * Math.PI / 2;
      if (tile === 'wall') {
        const wall = place(this.assets.manifest.wall.model, x, y, .02, .98);
        wall.scale.y = y === height - 1 ? .24 : (x === 0 || y === 0 || x === width - 1 ? 1 : .56);
        if (y === 0 && x > 0 && x < width - 1 && x % 4 === 2) place('banner.glb', x, y, .05, 1);
      } else if (tile !== 'floor' && tile !== 'exit') {
        const marker = this.mesh(new THREE.BoxGeometry(.7, .09, .7), stone(0xa5599a), this.board, x - (width - 1) / 2, .12, y - (height - 1) / 2);
        marker.rotation.y = Math.PI / 4;
      }
    }));
    const corners = new Set([`0,0`, `${width - 1},0`, `0,${height - 1}`, `${width - 1},${height - 1}`]);
    for (const corner of corners) {
      const [x, y] = corner.split(',').map(Number);
      if (tiles[y][x] !== 'wall') continue;
      place('column.glb', x, y, .05, 1.15);
      const px = x - (width - 1) / 2, pz = y - (height - 1) / 2;
      const light = new THREE.PointLight(0xffb450, 3, 4, 2);
      light.position.set(px, 1.55, pz); this.board.add(light);
      const flame = this.mesh(new THREE.IcosahedronGeometry(.105, 0), new THREE.MeshBasicMaterial({color: 0xffd89a}), this.board, px, 1.47, pz);
      this.effects.push({flame, light, phase: x + y});
    }
    for (let i = 0; i < 10; i++) {
      const a = i * 2.399;
      place('rocks.glb', (width - 1) / 2 + Math.cos(a) * (width / 2 + 1), (height - 1) / 2 + Math.sin(a) * (height / 2 + 1), -1.1, .2 + (i % 3) * .1);
    }
    const lines = [];
    for (let x = 0; x <= width; x++) lines.push(x - width / 2, .08, -height / 2, x - width / 2, .08, height / 2);
    for (let y = 0; y <= height; y++) lines.push(-width / 2, .08, y - height / 2, width / 2, .08, y - height / 2);
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(lines, 3));
    this.grid = new THREE.LineSegments(geometry, new THREE.LineBasicMaterial({color: 0xa9eedb, transparent: true, opacity: .6}));
    this.grid.visible = !!this.gridVisible; this.board.add(this.grid);
    const radius = Math.max(width, height) + 3;
    Object.assign(this.sun.shadow.camera, {left: -radius, right: radius, top: radius, bottom: -radius, near: .5, far: radius * 4});
    this.sun.shadow.camera.updateProjectionMatrix();
    this.fit();
  }
  sphinxStatue() {
    const group = new THREE.Group();
    const gold = () => new THREE.MeshStandardMaterial({color: 0xd9b373, roughness: .85});
    const blue = () => new THREE.MeshStandardMaterial({color: 0x28586a, roughness: .8});
    this.mesh(new THREE.BoxGeometry(.65, .32, .66), gold(), group, 0, .26, -.05);
    for (const x of [-.23, .23]) this.mesh(new THREE.BoxGeometry(.19, .17, .7), gold(), group, x, .09, .12);
    this.mesh(new THREE.BoxGeometry(.6, .49, .28), blue(), group, 0, .67, .15);
    this.mesh(new THREE.BoxGeometry(.35, .4, .33), gold(), group, 0, .67, .2);
    this.mesh(new THREE.BoxGeometry(.6, .08, .32), gold(), group, 0, .93, .16);
    for (const x of [-.1, .1]) this.mesh(new THREE.BoxGeometry(.06, .04, .015), blue(), group, x, .73, .374);
    this.mesh(new THREE.BoxGeometry(.07, .15, .05), blue(), group, 0, .46, .38);
    return group;
  }
  makeEntity(entity) {
    const spec = Object.hasOwn(this.assets.manifest, entity.appearance) ? this.assets.manifest[entity.appearance] : {};
    const root = new THREE.Group();
    const visual = spec.procedural === 'sphinx' ? this.sphinxStatue() : spec.model ? this.model(spec.model) : this.mesh(new THREE.OctahedronGeometry(.3), new THREE.MeshStandardMaterial({color: 0xc97ebe}), new THREE.Group());
    if (spec.model || spec.procedural) {
      const bounds = new THREE.Box3().setFromObject(visual);
      const scale = (spec.height ?? .6) / Math.max(bounds.max.y - bounds.min.y, .001);
      visual.scale.setScalar(scale);
      visual.position.y = -bounds.min.y * scale;
    } else visual.position.y = .4;
    root.add(visual); this.world.add(root);
    const item = {root, visual, spec, appearance: entity.appearance, cell: {...entity}, phase: entity.x * 2 + entity.y, baseY: visual.position.y};
    if (spec.animation) {
      const clips = this.assets.models.get(spec.model).animations;
      const idle = clips.find(clip => clip.name.toLowerCase() === spec.animation);
      if (idle) {
        item.mixer = new THREE.AnimationMixer(visual);
        item.idle = item.mixer.clipAction(idle); item.idle.play();
        const walk = clips.find(clip => clip.name.toLowerCase() === 'walk');
        if (walk) { item.walk = item.mixer.clipAction(walk); item.walk.play(); item.walk.enabled = false; }
      }
    }
    if (spec.effect === 'hero') { this.ring(root, .34, 0xf4d08e, .025); visual.rotation.y = Math.PI / 4; }
    if (spec.effect === 'float') this.ring(root, .3, 0x76e7dc, .025);
    if (spec.effect === 'portal') {
      visual.rotation.y = Math.PI;
      item.portal = this.mesh(new THREE.TorusGeometry(.44, .035, 8, 48), new THREE.MeshBasicMaterial({color: 0x98ffea}), root, 0, 1, -.22);
      this.mesh(new THREE.CircleGeometry(.4, 48), new THREE.MeshBasicMaterial({color: 0x59d4c6, transparent: true, opacity: .17, side: THREE.DoubleSide, depthWrite: false}), root, 0, 1, -.22);
    }
    root.position.set(entity.x - (this.width - 1) / 2, .06, entity.y - (this.height - 1) / 2);
    return item;
  }
  update(state) {
    const key = terrainKey(state), sameLevel = this.key === key;
    if (!sameLevel) { this.buildTerrain(state); this.key = key; }
    const actors = sceneEntities(state), ids = new Set(actors.map(e => e.id));
    for (const [id, item] of this.entities) if (!ids.has(id)) { this.removeEntity(item); this.entities.delete(id); }
    for (const entity of actors) {
      let item = this.entities.get(entity.id);
      if (item && item.appearance !== entity.appearance) { this.removeEntity(item); this.entities.delete(entity.id); item = null; }
      if (!item) { item = this.makeEntity(entity); this.entities.set(entity.id, item); }
      const target = new THREE.Vector3(entity.x - (this.width - 1) / 2, .06, entity.y - (this.height - 1) / 2);
      const moved = entity.x !== item.cell.x || entity.y !== item.cell.y;
      if (moved) {
        item.visual.rotation.y = Math.atan2(entity.x - item.cell.x, entity.y - item.cell.y);
        if (this.active && !document.hidden && !this.motion.matches && shouldAnimate(item.cell, entity, this.state?.turn, state.turn, sameLevel)) {
          item.move = {from: item.root.position.clone(), to: target, start: performance.now()};
        } else { item.move = null; item.root.position.copy(target); }
      } else if (this.state && state.turn < this.state.turn) { item.move = null; item.root.position.copy(target); }
      item.cell = {...entity};
    }
    this.state = state;
    this.schedule();
  }
  snap() {
    for (const item of this.entities.values()) if (item.move) { item.root.position.copy(item.move.to); item.move = null; }
  }
  fit() {
    if (this.disposed) return;
    const rect = this.canvas.parentElement.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    this.renderer.setSize(rect.width, rect.height, false);
    const aspect = rect.width / rect.height;
    const distance = Math.max(24, this.width + this.height);
    this.camera.position.set(0, distance, distance * 2 / 3);
    this.camera.far = distance * 5;
    this.camera.lookAt(0, 0, 0); this.camera.updateMatrixWorld();
    const corners = [];
    for (const x of [-this.width / 2 - .5, this.width / 2 + .5]) for (const z of [-this.height / 2 - .5, this.height / 2 + .5]) for (const y of [-1.1, 1.8]) corners.push(new THREE.Vector3(x, y, z).applyMatrix4(this.camera.matrixWorldInverse));
    const halfX = Math.max(...corners.map(p => Math.abs(p.x)));
    const halfY = Math.max(...corners.map(p => Math.abs(p.y)));
    const half = Math.max(halfY * 1.1, halfX / aspect * 1.1) / this.zoom;
    Object.assign(this.camera, {left: -half * aspect, right: half * aspect, top: half, bottom: -half});
    this.camera.updateProjectionMatrix();
    this.schedule();
  }
  setGridVisible(visible) { this.gridVisible = visible; if (this.grid) this.grid.visible = visible; this.schedule(); }
  zoomBy(delta) { this.zoom = THREE.MathUtils.clamp(this.zoom + delta, .75, 1.5); this.fit(); }
  resetZoom() { this.zoom = 1; this.fit(); }
  setActive(active) { this.active = active; this.snap(); if (active) this.fit(); this.schedule(); }
  schedule() {
    cancelAnimationFrame(this.raf);
    if (!this.active || document.hidden || this.disposed) { this.snap(); return; }
    this.raf = requestAnimationFrame(now => this.draw(now));
  }
  draw(now) {
    if (!this.active || this.disposed || document.hidden) return;
    const dt = Math.min((now - (this.last ?? now)) / 1000, .05); this.last = now;
    const t = this.motion.matches ? 0 : now / 1000;
    for (const item of this.entities.values()) {
      if (item.move) {
        const progress = Math.min(1, (now - item.move.start) / 140);
        item.root.position.lerpVectors(item.move.from, item.move.to, progress * progress * (3 - 2 * progress));
        if (progress === 1) item.move = null;
      }
      if (item.walk) { item.walk.enabled = !!item.move; item.idle.enabled = !item.move; }
      item.mixer?.update(this.motion.matches ? 0 : dt);
      if (item.spec.effect === 'float') { item.visual.position.y = item.baseY + .15 + Math.sin(t * 2 + item.phase) * .045; item.visual.rotation.y = t * .4 + item.phase; }
      if (item.portal) item.portal.scale.setScalar(1 + Math.sin(t * 2) * .025);
    }
    for (const {flame, light, phase} of this.effects) { flame.scale.setScalar(1 + Math.sin(t * 5 + phase) * .12); light.intensity = 3 + Math.sin(t * 5 + phase) * .4; }
    this.dust.rotation.y = t * .012;
    this.renderer.render(this.scene, this.camera);
    if (!this.motion.matches) this.raf = requestAnimationFrame(time => this.draw(time));
  }
  dispose() {
    this.disposed = true;
    cancelAnimationFrame(this.raf);
    this.observer.disconnect();
    document.removeEventListener('visibilitychange', this.onVisibility);
    this.motion.removeEventListener('change', this.onMotion);
    this.canvas.removeEventListener('webglcontextlost', this.onContextLost);
    for (const item of this.entities.values()) this.removeEntity(item);
    this.entities.clear();
    this.release(this.board); this.release(this.dust);
    this.sun.shadow.map?.dispose();
    this.renderer.dispose(); this.renderer.forceContextLoss();
    this.scene.clear();
  }
}
