import {createServer} from 'node:http';
import {readFile, realpath} from 'node:fs/promises';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {resolve, extname, sep} from 'node:path';
import {DemoWorld} from './demo-world.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
const mime = {'.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.json': 'application/json', '.png': 'image/png', '.glb': 'model/gltf-binary', '.md': 'text/plain; charset=utf-8', '.txt': 'text/plain; charset=utf-8'};
mime['.svg'] = 'image/svg+xml';
const json = (res, status, body) => { res.writeHead(status, {'Content-Type': 'application/json', 'Cache-Control': 'no-store'}); res.end(JSON.stringify(body)); };
const error = (res, status, code, message) => json(res, status, {error: {code, message}});
async function body(req) {
  const chunks = []; let size = 0;
  for await (const chunk of req) { size += chunk.length; if (size > 65536) throw new Error('Request body exceeds 64 KiB.'); chunks.push(chunk); }
  return Buffer.concat(chunks).toString('utf8');
}

export function createRendererServer({demo = false, api = ''} = {}) {
  if (demo && api) throw new Error('Choose --demo or --api, not both.');
  const target = api ? new URL(api.endsWith('/') ? api : `${api}/`) : null;
  if (target && !['http:', 'https:'].includes(target.protocol)) throw new Error('API URL must use HTTP or HTTPS.');
  const world = demo ? new DemoWorld() : null;
  return createServer(async (req, res) => {
    try {
      const url = new URL(req.url, 'http://localhost');
      if (url.pathname.startsWith('/api/')) {
        if (!['/api/state', '/api/actions', '/api/answer', '/api/cancel'].includes(url.pathname)) return error(res, 404, 'not_found', 'Unknown API route.');
        const method = url.pathname === '/api/state' ? 'GET' : 'POST';
        if (req.method !== method) return error(res, 405, 'method_not_allowed', `Use ${method}.`);
        if (target) {
          try {
            const response = await fetch(new URL(url.pathname.slice(1), target), {method, headers: {Accept: 'application/json', ...(method === 'POST' ? {'Content-Type': req.headers['content-type'] ?? ''} : {})}, ...(method === 'POST' ? {body: await body(req)} : {}), signal: AbortSignal.timeout(4500), redirect: 'error'});
            const payload = Buffer.from(await response.arrayBuffer());
            res.writeHead(response.status, {'Content-Type': response.headers.get('content-type') ?? 'application/json', 'Cache-Control': 'no-store'}); res.end(payload);
          } catch { error(res, 503, 'engine_unavailable', 'Cannot reach the configured Python API. Check its address and startup command.'); }
          return;
        }
        if (!world) return error(res, 503, 'engine_unavailable', 'No API configured. Start with --api http://127.0.0.1:8000 or use npm run demo.');
        if (method === 'GET') return json(res, 200, world.frame());
        if (req.headers['content-type']?.split(';')[0].trim().toLowerCase() !== 'application/json') return error(res, 415, 'unsupported_media_type', 'Content-Type must be application/json.');
        let value;
        try { value = JSON.parse(await body(req)); } catch { return error(res, 400, 'invalid_json', 'Request body must be valid JSON.'); }
        const result = world.action(value); return json(res, result.status, result.body);
      }
      if (!['GET', 'HEAD'].includes(req.method)) return error(res, 405, 'method_not_allowed', 'Use GET or HEAD for static files.');
      const pathname = decodeURIComponent(url.pathname === '/' ? '/index.html' : url.pathname);
      // Only the supplied front and fixtures are exposed, not teacher tools or tests.
      const relative = pathname.slice(1);
      if (!['index.html', 'preview.html', 'style.css', 'app.js', 'preview.js'].includes(relative) && !/^(src|assets|vendor|fixtures|docs)\//.test(relative)) return error(res, 404, 'not_found', 'File not found.');
      const file = await realpath(resolve(root, relative));
      if (!file.startsWith(root.endsWith(sep) ? root : root + sep)) return error(res, 404, 'not_found', 'File not found.');
      const bytes = await readFile(file);
      res.writeHead(200, {'Content-Type': mime[extname(file)] ?? 'application/octet-stream', 'Cache-Control': 'no-store'});
      res.end(req.method === 'HEAD' ? undefined : bytes);
    } catch (failure) {
      if (['ENOENT', 'EISDIR', 'ENOTDIR'].includes(failure.code) || failure instanceof URIError) error(res, 404, 'not_found', 'File not found.');
      else error(res, 500, 'internal_error', 'Local server could not complete this request.');
    }
  });
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const args = process.argv.slice(2);
  let demo = false, api = '', port = 8080;
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--demo') demo = true;
    else if (args[i] === '--api') { api = args[++i]; if (!api) throw new Error('--api requires an address.'); }
    else if (args[i] === '--port') port = Number(args[++i]);
    else throw new Error(`Unknown option: ${args[i]}`);
  }
  if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error('Port must be between 1 and 65535.');
  const server = createRendererServer({demo, api});
  server.on('error', failure => { console.error(failure.message); process.exitCode = 1; });
  server.listen(port, '127.0.0.1', () => {
    console.log(`Gridworld: http://127.0.0.1:${port}/${demo ? '?demo=1' : ''}`);
    console.log(demo ? 'Teacher demo. Restart this process for a new game.' : api ? `Proxying /api to ${api}` : 'Static renderer. Configure an API or open /preview.html for fixtures.');
  });
}
