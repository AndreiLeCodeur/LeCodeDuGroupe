const assetsURL = new URL('../assets/', import.meta.url);

async function manifest(name) {
  const response = await fetch(new URL(name, assetsURL));
  if (!response.ok) throw new Error(`Cannot load ${name} (HTTP ${response.status}).`);
  return response.json();
}

export async function loadSprites() {
  const entries = await manifest('manifest2d.json');
  const sprites = new Map();
  const missing = [];
  await Promise.all(Object.entries(entries).map(async ([key, filename]) => {
    const image = new Image();
    image.src = new URL(`sprites/${filename}`, assetsURL).href;
    try { await image.decode(); sprites.set(key, image); }
    catch { missing.push(key); }
  }));
  return {sprites, missing};
}

export async function loadModels() {
  const [{GLTFLoader}, entries] = await Promise.all([import('../vendor/GLTFLoader.js'), manifest('manifest3d.json')]);
  const names = new Set([...Object.values(entries).map(spec => spec.model).filter(Boolean), 'floor-detail.glb', 'column.glb', 'banner.glb', 'rocks.glb']);
  const loader = new GLTFLoader();
  const models = new Map();
  const results = await Promise.allSettled([...names].map(async name => {
    const model = await loader.loadAsync(new URL(`models/${name}`, assetsURL).href);
    models.set(name, model);
  }));
  const dispose = () => {
    const geometries = new Set(), materials = new Set(), textures = new Set();
    for (const model of models.values()) model.scene.traverse(part => {
      if (part.geometry) geometries.add(part.geometry);
      for (const material of Array.isArray(part.material) ? part.material : [part.material]) {
        if (!material) continue;
        materials.add(material);
        for (const value of Object.values(material)) if (value?.isTexture) textures.add(value);
      }
    });
    geometries.forEach(value => value.dispose());
    materials.forEach(value => value.dispose());
    textures.forEach(value => { value.dispose(); value.source?.data?.close?.(); });
    models.clear();
  };
  const failure = results.find(result => result.status === 'rejected');
  if (failure) { dispose(); throw failure.reason; }
  return {manifest: entries, models, dispose};
}
